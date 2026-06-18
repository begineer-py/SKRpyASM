import abc
import importlib
import inspect
import logging
import re
from typing import (
    Annotated,
    Any,
    AsyncIterable,
    AsyncIterator,
    ClassVar,
    Dict,
    Literal,
    Sequence,
    Type,
    TypedDict,
    cast,
    overload,
)

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    format_document,
)
from langchain_core.retrievers import (
    BaseRetriever,
    RetrieverOutput,
)
from langchain_core.runnables import (
    Runnable,
    RunnableBranch,
    RunnableConfig,
)
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.graph import END, StateGraph, add_messages
from langgraph.errors import GraphRecursionError
from pydantic import BaseModel

from apps.ai_assistant.decorators import with_cast_id
from apps.ai_assistant.exceptions import (
    AIAssistantMisconfiguredError,
)
from apps.ai_assistant.helpers.django_messages import save_django_messages
from apps.ai_assistant.langchain.tools import tool as tool_decorator




class ProviderConfig(TypedDict):
    langchain_module: str
    llm_class: str


ProviderName = Literal["openai", "anthropic", "google", "groq", "ollama", "mistral", "together"]

PROVIDER_LLM_LOOKUP: dict[ProviderName, ProviderConfig] = {
    "openai": {
        "langchain_module": "langchain_openai",
        "llm_class": "ChatOpenAI",
    },
    "anthropic": {
        "langchain_module": "langchain_anthropic",
        "llm_class": "ChatAnthropic",
    },
    "google": {
        "langchain_module": "langchain_google_genai",
        "llm_class": "ChatGoogleGenerativeAI",
    },
    # ─── 以下是你可以直接加塞的熱門供應商 ───
    "groq": {
        # 極速推理服務（Llama 3, Mixtral）
        "langchain_module": "langchain_groq",
        "llm_class": "ChatGroq",
    },
    "ollama": {
        # 本地跑開源模型（Llama 3, Qwen, Mistral）
        "langchain_module": "langchain_ollama",
        "llm_class": "ChatOllama",
    },
    "mistral": {
        # 歐洲最強開源大模型
        "langchain_module": "langchain_mistralai",
        "llm_class": "ChatMistralAI",
    },
    "together": {
        # 雲端開源模型託管商
        "langchain_module": "langchain_together",
        "llm_class": "ChatTogether",
    },
}

class AIAssistant(abc.ABC):  # noqa: F821
    """Base class for AI Assistants. Subclasses must define at least the following attributes:

    * id: str
    * name: str
    * instructions: str
    * model: str

    Subclasses can override the public methods to customize the behavior of the assistant.\n
    Tools can be added to the assistant by decorating methods with `@method_tool`.\n
    Check the docs Tutorial for more info on how to build an AI Assistant.
    """

    id: ClassVar[str]  # noqa: A003
    """Class variable with the id of the assistant. Used to select the assistant to use.\n
    Must be unique across the whole Django project and match the pattern '^[a-zA-Z0-9_-]+$'."""
    name: ClassVar[str]
    """Class variable with the name of the assistant.
    Should be a friendly name to optionally display to users."""
    instructions: str
    """Instructions for the AI assistant knowing what to do. This is the LLM system prompt."""
    model: str
    """LLM model name to use for the assistant.\n
    Should be a valid model name from OpenAI, because the default `get_llm` method uses OpenAI.\n
    `get_llm` can be overridden to use a different LLM implementation.
    """
    temperature: float | None = 1.0
    """Temperature to use for the assistant LLM model.\n
    Defaults to `1.0`.\n
    When `None`, the temperature parameter is omitted when constructing the BaseChatModel
    in the `get_llm` method.
    """
    tool_max_concurrency: int = 1
    """Maximum number of tools to run concurrently / in parallel.\nDefaults to `1` (no concurrency)."""
    recursion_limit: int = 150
    """LangGraph recursion limit. Defaults to `150` to allow for longer workflows."""
    stop_on_waiting_async: bool = False
    """When True, forces the agent loop to end after 2+ WAITING_FOR_ASYNC tool results,
    preventing infinite polling loops for async scanner tasks."""
    max_consecutive_same_tool: int = 0
    """When > 0, forces the agent loop to end if the same tool is called this many
    times in a row with no other tool calls in between. 0 = no limit."""
    has_rag: bool = False
    """Whether the assistant uses RAG (Retrieval-Augmented Generation) or not.\n
    Defaults to `False`.
    When True, the assistant will use a retriever to get documents to provide as context to the LLM.
    Additionally, the assistant class should implement the `get_retriever` method to return
    the retriever to use."""
    structured_output: Dict[str, Any] | Type[BaseModel] | Type | None = None
    """Structured output to use for the assistant.\n
    Defaults to `None`.
    When not `None`, the assistant will return a structured output in the provided format.
    See https://python.langchain.com/v0.3/docs/how_to/structured_output/ for the available formats.
    """
    _user: Any | None
    """The current user the assistant is helping. A model instance.\n
    Set by the constructor.
    When API views are used, this is set to the current request user.\n
    Can be used in any `@method_tool` to customize behavior."""
    _request: Any | None
    """The current Django request the assistant was initialized with. A request instance.\n
    Set by the constructor.\n
    Can be used in any `@method_tool` to customize behavior."""
    _view: Any | None
    """The current Django view the assistant was initialized with. A view instance.\n
    Set by the constructor.\n
    Can be used in any `@method_tool` to customize behavior."""
    _init_kwargs: dict[str, Any]
    """Extra keyword arguments passed to the constructor.\n
    Set by the constructor.\n
    Can be used in any `@method_tool` to customize behavior."""
    _method_tools: Sequence[BaseTool]
    """List of `@method_tool` tools the assistant can use. Automatically set by the constructor."""
    _provider: ProviderName
    """The provider key used to resolve and import the chat model class."""

    _registry: ClassVar[dict[str, type["AIAssistant"]]] = {}
    """Registry of all AIAssistant subclasses by their id.\n
Automatically populated by when a subclass is declared.\n
Use `get_cls_registry` and `get_cls` to access the registry."""

    _bg_tasks: ClassVar[set[Any]] = set()
    """Background asyncio tasks for astream producer-consumer.\n
Holds refs so tasks aren't GC'd before completion."""

    DEFAULT_DOCUMENT_PROMPT: ClassVar[PromptTemplate] = PromptTemplate.from_template(
        "{page_content}"
    )
    DEFAULT_DOCUMENT_SEPARATOR: ClassVar[str] = "\n\n"

    def __init__(
        self,
        *,
        user=None,
        request=None,
        view=None,
        provider: ProviderName = "openai",
        **kwargs: Any,
    ):
        """Initialize the AIAssistant instance.\n
        Optionally set the current user, request, and view for the assistant.\n
        Those can be used in any `@method_tool` to customize behavior.\n

        Args:
            user (Any | None): The current user the assistant is helping. A model instance.
                Defaults to `None`. Stored in `self._user`.
            request (Any | None): The current Django request the assistant was initialized with.
                A request instance. Defaults to `None`. Stored in `self._request`.
            view (Any | None): The current Django view the assistant was initialized with.
                A view instance. Defaults to `None`. Stored in `self._view`.
            provider (ProviderName): The provider used to build the LLM instance.
                Requires the corresponding langchain module to be installed (see `PROVIDER_LLM_LOOKUP`).
                Defaults to `openai`. Stored in `self._provider`.
            **kwargs: Extra keyword arguments passed to the constructor. Stored in `self._init_kwargs`.
        """

        self._user = user
        self._request = request
        self._view = view
        self._provider = provider
        self._init_kwargs = kwargs

        self._set_method_tools()

    def __init_subclass__(cls, **kwargs: Any):
        """Called when a class is subclassed from AIAssistant.

        This method is automatically invoked when a new subclass of AIAssistant
        is created. It allows AIAssistant to perform additional setup or configuration
        for the subclass, such as registering the subclass in a registry.

        Args:
            cls (type): The newly created subclass.
            **kwargs: Additional keyword arguments passed during subclass creation.
        """
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "id"):
            raise AIAssistantMisconfiguredError(f"Assistant id is not defined at {cls.__name__}")
        if cls.id is None:
            raise AIAssistantMisconfiguredError(f"Assistant id is None at {cls.__name__}")
        if not re.match(r"^[a-zA-Z0-9_-]+$", cls.id):
            # id should match the pattern '^[a-zA-Z0-9_-]+$ to support as_tool in OpenAI
            raise AIAssistantMisconfiguredError(
                f"Assistant id '{cls.id}' does not match the pattern '^[a-zA-Z0-9_-]+$'"
                f"at {cls.__name__}"
            )

        cls._registry[cls.id] = cls

    def _set_method_tools(self):
        # Find tool methods (decorated with `@method_tool` from apps.ai_assistant/tools.py):
        members = inspect.getmembers(
            self,
            predicate=lambda m: inspect.ismethod(m) and getattr(m, "_is_tool", False),
        )
        tool_methods = [m for _, m in members]

        # Sort tool methods by the order they appear in the source code,
        # since this can be meaningful:
        tool_methods.sort(key=lambda m: inspect.getsourcelines(m)[1])

        # Transform tool methods into tool objects:
        tools = []
        for method in tool_methods:
            if hasattr(method, "_tool_maker_args"):
                tool = tool_decorator(
                    *method._tool_maker_args,
                    **method._tool_maker_kwargs,
                )(method)
            else:
                tool = tool_decorator(method)
            tools.append(cast(BaseTool, tool))

        # 自動剝離欄位：self（綁定方法）+ 內部 ID 欄位（不對 LLM 暴露）
        # overview_id / thread_id / parent_thread_id 由 agent instance 自動注入，
        # 避免 LLM 幻覺猜測 ID（問題 ②③）。agent instance 的 _agent_overview_id、
        # _current_invoke_thread_id、_caller_thread_id 於 _set_auto_injected_ids() 解析。
        _hidden_fields = {"self", "overview_id", "thread_id", "parent_thread_id"}
        for tool in tools:
            if tool.args_schema:
                if isinstance(tool.args_schema.__fields_set__, set):
                    tool.args_schema.__fields_set__ -= _hidden_fields
                for fld in _hidden_fields:
                    tool.args_schema.__fields__.pop(fld, None)

        self._method_tools = tools

    def _set_auto_injected_ids(self):
        """解析本 agent instance 對應的 overview_id / thread_id / caller_thread_id，
        供工具呼叫時自動注入。在 invoke / _run_as_tool 進入點與 get_target_context /
        create_overview 等工具內會更新 _agent_overview_id。

        應於 invoke() 與 _run_as_tool() 開始時呼叫。
        """
        # thread_id（自身）：優先使用 _current_invoke_thread_id，其次 _thread
        if getattr(self, "_current_invoke_thread_id", None) is None:
            thread = getattr(self, "_thread", None)
            if thread is not None and getattr(thread, "id", None) is not None:
                self._current_invoke_thread_id = thread.id

    @classmethod
    def get_cls_registry(cls) -> dict[str, type["AIAssistant"]]:
        """Get the registry of AIAssistant classes.

        Returns:
            dict[str, type[AIAssistant]]: A dictionary mapping assistant ids to their classes.
        """
        return cls._registry

    @classmethod
    def get_cls(cls, assistant_id: str) -> type["AIAssistant"]:
        """Get the AIAssistant class for the given assistant ID.

        Args:
            assistant_id (str): The ID of the assistant to get.
        Returns:
            type[AIAssistant]: The AIAssistant subclass for the given ID.
        """
        return cls.get_cls_registry()[assistant_id]

    @classmethod
    def clear_cls_registry(cls: type["AIAssistant"]) -> None:
        """Clear the registry of AIAssistant classes."""

        cls._registry.clear()

    def get_instructions(self) -> str:
        """Get the instructions for the assistant. By default, this is the `instructions` attribute.\n
        Override the `instructions` attribute or this method to use different instructions.

        Returns:
            str: The instructions for the assistant, i.e., the LLM system prompt.
        """
        return self.instructions

    def get_model(self) -> str:
        """Get the LLM model name for the assistant. By default, this is the `model` attribute.\n
        Used by the `get_llm` method to create the LLM instance.\n
        Override the `model` attribute or this method to use a different LLM model.

        Returns:
            str: The LLM model name for the assistant.
        """
        return self.model

    def get_temperature(self) -> float | None:
        """Get the temperature to use for the assistant LLM model.
        By default, this is the `temperature` attribute, which is `1.0` by default.\n
        Used by the `get_llm` method to create the LLM instance.\n
        Override the `temperature` attribute or this method to use a different temperature.\n
        Returning `None` is a valid option, particularly for models that do not support
        temperature control, allowing the parameter to be omitted in the `get_llm` method.\n

        Returns:
            float | None: The temperature to use for the assistant LLM model.
        """
        return self.temperature

    def get_model_kwargs(self) -> dict[str, Any]:
        """Get additional keyword arguments to pass to the LLM model constructor.\n
        Used by the `get_llm` method to create the LLM instance.\n
        Override this method to pass additional keyword arguments to the LLM model constructor.

        Returns:
            dict[str, Any]: Additional keyword arguments to pass to the LLM model constructor.
        """
        return {}

    def _import_llm_class(self):
        provider = PROVIDER_LLM_LOOKUP.get(self._provider)
        if not provider:
            valid_providers_list = PROVIDER_LLM_LOOKUP.keys()
            raise AIAssistantMisconfiguredError(
                f"Invalid provider={self._provider}, please use one "
                f"of the supported providers: {valid_providers_list}"
            )

        # Performs a deferred import of the LLM class that corresponds to
        # the self._provider value and returns it.
        try:
            langchain_module_str = provider["langchain_module"]
            langchain_module = importlib.import_module(f"{langchain_module_str}")
        except ImportError as err:
            raise ImportError(
                f"'{langchain_module_str}' is required to use this provider. "
                f"Install it with: pip install django-ai-assistant[{self._provider}]"
            ) from err

        llm_class_str = provider["llm_class"]
        try:
            return getattr(langchain_module, llm_class_str)
        except AttributeError as err:
            raise ImportError(
                f"'{llm_class_str}' is not a valid LLM class for provider '{self._provider}'."
            ) from err

    def get_llm(self) -> BaseChatModel:
        """Get the LangChain LLM instance for the assistant.
        By default, this uses the OpenAI implementation.\n
        `get_model`, `get_temperature`, and `get_model_kwargs` are used to create the LLM instance.\n
        Override this method to use a different LLM implementation.

        Returns:
            BaseChatModel: The LLM instance for the assistant.
        """
        model = self.get_model()
        temperature = self.get_temperature()
        model_kwargs = self.get_model_kwargs()

        llm_class = self._import_llm_class()

        if temperature is not None:
            return llm_class(
                model=model,
                temperature=temperature,
                model_kwargs=model_kwargs,
            )
        else:
            return llm_class(
                model=model,
                model_kwargs=model_kwargs,
            )

    def get_structured_output_llm(self) -> Runnable:
        """Get the LLM model to use for the structured output.

        Returns:
            BaseChatModel: The LLM model to use for the structured output.
        """
        if not self.structured_output:
            raise ValueError("structured_output is not defined")

        llm = self.get_llm()

        method = "json_mode"
        if self._provider == "openai":
            # When using ChatOpenAI, it's better to use json_schema method
            # because it enables strict mode.
            # https://platform.openai.com/docs/guides/structured-outputs
            method = "json_schema"

        return llm.with_structured_output(self.structured_output, method=method)

    def get_tools(self) -> Sequence[BaseTool]:
        """Get the list of method tools the assistant can use.
        By default, this is the `_method_tools` attribute, which are all `@method_tool`s.\n
        Override and call super to add additional tools,
        such as [any langchain_community tools](https://python.langchain.com/v0.3/docs/integrations/tools/).

        Returns:
            Sequence[BaseTool]: The list of tools the assistant can use.
        """
        return self._method_tools

    def _internal_generate_summary(self, content: str, tool_name: str = "tool") -> str:
        """使用 compression_agent 輕量 LLM 產生工具輸出摘要（比主模型快且便宜）。"""
        try:
            from apps.core.llms import get_llm_instance
            from langchain_core.messages import HumanMessage
            # compression_agent 優先（便宜），fallback 到主模型
            try:
                llm = get_llm_instance(agent_id="compression_agent", temperature=0)
            except Exception:
                llm = self.get_llm()
            prompt = (
                f"Summarize this {tool_name} tool output in max 300 chars. "
                "Preserve: IPs, ports, URLs, findings, error messages, CVEs.\n\n"
                f"Output:\n{content[:5000]}\n\nSummary:"
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            return (resp.content if hasattr(resp, 'content') else str(resp))[:400]
        except Exception as e:
            logger.error(f"Internal summary generation failed: {e}")
            return f"[{tool_name}: {str(content)[:150]}...]"

    def _generate_page_breakdown(self, content: str) -> list:
        """使用 compression_agent LLM 將超長內容拆分為結構化頁面。

        返回 [{"title": str, "content": str}, ...]
        用於 read_content_blob 的 page 參數分頁查詢，避免死循環。
        """
        try:
            from apps.core.llms import get_llm_instance
            from langchain_core.messages import HumanMessage
            import json

            try:
                llm = get_llm_instance(agent_id="compression_agent", temperature=0)
            except Exception:
                llm = self.get_llm()

            prompt = (
                "你是一個文檔結構分析專家。請將以下內容按語義結構拆分為多個頁面(page)。\n"
                "要求：\n"
                "1. 按內容主題自然分頁（而非按字符硬切）\n"
                "2. 每頁提供一個簡短的 title（20 字以內）\n"
                "3. 每頁 content 不超過 4000 字\n"
                "4. 輸出為 JSON 數組格式：[{\"title\": \"...\", \"content\": \"...\"}]\n"
                "5. 只輸出 JSON，不要額外的解釋\n\n"
                f"=== 原始內容（截取前 50000 字）===\n{content[:50000]}"
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            text = resp.content if hasattr(resp, 'content') else str(resp)
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            pages = json.loads(text)
            return pages if isinstance(pages, list) else []
        except Exception as e:
            logger.error(f"Page breakdown generation failed: {e}")
            return []

    def get_callbacks(self) -> Sequence[BaseCallbackHandler]:
        """Get the list of callback handlers for monitoring and logging assistant execution.
        By default, returns an empty list (no callbacks enabled).

        Callbacks are used to hook into the LangChain execution pipeline to monitor:
        - Tool calls (on_tool_start, on_tool_end, on_tool_error)
        - Agent actions (on_agent_action)
        - Chain execution (on_chain_start, on_chain_end)
        - LLM calls (on_llm_start, on_llm_end)

        This allows for logging, metrics collection, and observability without requiring
        the AI model to actively call logging methods.

        Override this method in subclasses to provide custom callbacks.

        Returns:
            Sequence[BaseCallbackHandler]: The list of callback handlers to use.

        Example:
            class MyAssistant(AIAssistant):
                def get_callbacks(self):
                    from myapp.callbacks import MyCustomHandler
                    return [MyCustomHandler()]
        """
        return []

    def _get_event_thread(self):
        from apps.core.models import Thread

        thread = getattr(self, "_thread", None)
        if thread is not None:
            return thread
        thread_id = getattr(self, "_current_invoke_thread_id", None)
        if not thread_id:
            return None
        return Thread.objects.filter(id=thread_id).first()

    def emit_thread_event(
        self,
        event_type: str,
        *,
        status: str | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
        node_name: str | None = None,
        tool_name: str | None = None,
    ) -> Any | None:
        """Allow tools to emit durable execution events.

        Dual-writes to both ExecutionEvent (for ExecutionTimelineViewer)
        and ThreadEvent (for ThreadEvent SSE streaming).
        """
        from apps.core.services import ExecutionService
        from apps.ai_assistant.services.events import AgentEventService

        graph = self._get_execution_graph()
        thread = self._get_event_thread()

        result = None
        if graph is not None:
            result = ExecutionService.emit_event(
                graph=graph,
                event_type=event_type,
                status=status,
                content=content,
                payload=payload,
            )

        AgentEventService.emit(
            thread=thread,
            event_type=event_type,
            status=status,
            content=content,
            payload=payload,
            node_name=node_name,
            tool_name=tool_name,
        )

        return result

    def _get_execution_graph(self):
        from apps.core.models import ExecutionGraph

        graph = getattr(self, "_execution_graph", None)
        if graph is not None:
            return graph
        graph_id = getattr(self, "_current_execution_graph_id", None)
        if not graph_id:
            return None
        return ExecutionGraph.objects.filter(id=graph_id).first()

    def get_document_separator(self) -> str:
        """Get the RAG document separator to use in the prompt. Only used when `has_rag=True`.\n
        Defaults to `"\\n\\n"`, which is the LangChain default.\n
        Override this method to use a different separator.

        Returns:
            str: a separator for documents in the prompt.
        """
        return self.DEFAULT_DOCUMENT_SEPARATOR

    def get_document_prompt(self) -> PromptTemplate:
        """Get the PromptTemplate template to use when rendering RAG documents in the prompt.
        Only used when `has_rag=True`.\n
        Defaults to `PromptTemplate.from_template("{page_content}")`, which is the LangChain default.\n
        Override this method to use a different template.

        Returns:
            PromptTemplate: a prompt template for RAG documents.
        """
        return self.DEFAULT_DOCUMENT_PROMPT

    def get_retriever(self) -> BaseRetriever:
        """Get the RAG retriever to use for fetching documents.\n
        Must be implemented by subclasses when `has_rag=True`.\n

        Returns:
            BaseRetriever: the RAG retriever to use for fetching documents.
        """
        raise NotImplementedError(
            f"Override the get_retriever with your implementation at {self.__class__.__name__}"
        )

    def get_contextualize_prompt(self) -> ChatPromptTemplate:
        """Get the contextualize prompt template for the assistant.\n
        This is used when `has_rag=True` and there are previous messages in the thread.
        Since the latest user question might reference the chat history,
        the LLM needs to generate a new standalone question,
        and use that question to query the retriever for relevant documents.\n
        By default, this is a prompt that asks the LLM to
        reformulate the latest user question without the chat history.\n
        Override this method to use a different contextualize prompt.\n
        See `get_history_aware_retriever` for how this prompt is used.\n

        Returns:
            ChatPromptTemplate: The contextualize prompt template for the assistant.
        """
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                # TODO: make history key configurable?
                MessagesPlaceholder("history"),
                # TODO: make input key configurable?
                ("human", "{input}"),
            ]
        )

    def get_history_aware_retriever(self) -> Runnable[dict, RetrieverOutput]:
        """Get the history-aware retriever LangChain chain for the assistant.\n
        This is used when `has_rag=True` to fetch documents based on the chat history.\n
        By default, this is a chain that checks if there is chat history,
        and if so, it uses the chat history to generate a new standalone question
        to query the retriever for relevant documents.\n
        When there is no chat history, it just passes the input to the retriever.\n
        Override this method to use a different history-aware retriever chain.

        Read more about the history-aware retriever in the
        [LangChain docs](https://python.langchain.com/v0.2/docs/how_to/qa_chat_history_how_to/).

        Returns:
            Runnable[dict, RetrieverOutput]: a history-aware retriever LangChain chain.
        """
        llm = self.get_llm()
        retriever = self.get_retriever()
        prompt = self.get_contextualize_prompt()

        # Based on create_history_aware_retriever:
        return RunnableBranch(
            (
                lambda x: not x.get("history", False),  # pyright: ignore[reportAttributeAccessIssue]
                # If no chat history, then we just pass input to retriever
                (lambda x: x["input"]) | retriever,
            ),
            # If chat history, then we pass inputs to LLM chain, then to retriever
            prompt | llm | StrOutputParser() | retriever,
        )

    @with_cast_id
    def as_graph(
        self, thread_id: Any | None = None, thread: Any | None = None
    ) -> Runnable[dict, dict]:
        """Create the LangGraph graph for the assistant.\n
        This graph is an agent that supports chat history, tool calling, and RAG (if `has_rag=True`).\n
        `as_graph` uses many other methods to create the graph for the assistant.
        Prefer to override the other methods to customize the graph for the assistant.
        Only override this method if you need to customize the graph at a lower level.

        If both arguments are `None`, an in-memory chat message history is used.

        Args:
            thread_id (Any | None): The thread ID for the chat message history.
            thread (Any | None): The thread object for the chat message history.

        Returns:
            the compiled graph
        """
        from apps.core.models import Thread

        llm = self.get_llm()
        tools = self.get_tools()

        if thread and thread.bound_overview_id:
            # 相容舊路徑：若 thread 已綁定 overview，同步到 agent instance
            if not getattr(self, "_agent_overview_id", None):
                self._agent_overview_id = thread.bound_overview_id

        # 無論 thread 是否綁定，都對「宣告過 overview_id 的工具」套用自動注入 wrap。
        # 策略：強制覆蓋——即使 LLM 企圖傳入 overview_id 也以 agent instance 的值為準，
        # 徹底避免 ID 幻覺（問題 ②）。
        _self_overview_id = getattr(self, "_agent_overview_id", None)
        wrapped_tools = []
        for tool in tools:
            # Check if tool expects overview_id（即使已從 public schema 剝離，
            # 函式簽名仍保留參數，故檢查 __signature__ 而非 args_schema）
            needs_ov_inject = False
            try:
                import inspect as _inspect
                sig_params = _inspect.signature(getattr(tool, "func", None) or getattr(tool, "coroutine", None)).parameters if hasattr(tool, "func") or hasattr(tool, "coroutine") else {}
                needs_ov_inject = "overview_id" in sig_params
            except Exception:
                pass
            # fallback：檢查 args_schema 是否原始簽名包含 overview_id
            if not needs_ov_inject and tool.args_schema:
                fields = getattr(tool.args_schema, "model_fields", getattr(tool.args_schema, "__fields__", {}))
                needs_ov_inject = "overview_id" in fields

            if needs_ov_inject:
                def _create_wrapped_func(t, agent_ref):
                    orig_func = getattr(t, "func", None)
                    if not orig_func:
                        return None

                    def _wrapped(*args, **kwargs):
                        # 延遲讀取——每次工具呼叫時從 agent instance 取最新值。
                        # as_graph() 階段 _agent_overview_id 可能仍為 None，
                        # 要等到 get_target_context / create_overview 執行後才會被設定。
                        current_ov = getattr(agent_ref, "_agent_overview_id", None)
                        if current_ov is not None:
                            kwargs["overview_id"] = current_ov
                        elif kwargs.get("overview_id") is None:
                            # fallback：thread.bound_overview_id（舊路徑相容）
                            bound_ov = getattr(getattr(agent_ref, "_thread", None), "bound_overview_id", None)
                            if bound_ov:
                                kwargs["overview_id"] = bound_ov
                        return orig_func(*args, **kwargs)
                    return _wrapped

                wrapped_func = _create_wrapped_func(tool, self)
                if wrapped_func:
                    new_tool = StructuredTool.from_function(
                        func=wrapped_func,
                        name=tool.name,
                        description=tool.description,
                        args_schema=tool.args_schema
                    )
                    wrapped_tools.append(new_tool)
                    continue

            wrapped_tools.append(tool)
        tools = wrapped_tools

        llm_with_tools = llm.bind_tools(tools) if tools else llm
        if thread is None and thread_id is not None:
            thread = Thread.objects.get(id=thread_id)

        class AgentState(TypedDict):
            messages: Annotated[list[AnyMessage], add_messages]
            input: str | None  # noqa: A003
            output: Any
            pending_tool_calls: list[dict[str, Any]]

        def setup(state: AgentState):
            system_prompt = self.get_instructions()
            if thread:
                # 不再對 LLM 暴露具體 Thread ID（問題 ②③）。
                # 委派子 Agent 時，spawn 工具會自動帶入 caller_thread_id。
                system_prompt += (
                    "\n\n[SYSTEM INFO]\n"
                    "You are running inside a managed conversation thread. "
                    "When you delegate long tasks to another agent via spawn_*_agent tools, "
                    "the platform automatically propagates your caller_thread_id — "
                    "you do NOT need to (and should not) pass any thread_id explicitly."
                )

                # Inject GlobalContextOverview into system prompt if available
                try:
                    overview = thread.global_overview
                    if overview.mission:
                        overview_block = (
                            f"\n\n[GLOBAL CONTEXT OVERVIEW]\n"
                            f"Mission: {overview.mission}\n"
                            f"Phase: {overview.current_phase}\n"
                        )
                        if overview.confirmed_vulnerabilities:
                            overview_block += (
                                f"Confirmed Vulnerabilities: "
                                f"{len(overview.confirmed_vulnerabilities)} items\n"
                            )
                        if overview.critical_artifacts:
                            overview_block += (
                                f"Critical Artifacts: "
                                f"{len(overview.critical_artifacts)} items\n"
                            )
                        system_prompt += overview_block
                except Exception:
                    pass

            return {"messages": [SystemMessage(content=system_prompt)]}

        def history(state: AgentState):
            messages = thread.get_messages(include_extra_messages=True) if thread else []
            if state["input"]:
                input_content = state["input"]
                already_present = any(
                    isinstance(m, HumanMessage) and m.content == input_content
                    for m in messages
                )
                if not already_present:
                    messages.append(HumanMessage(content=input_content))

            return {"messages": messages}

        def context_check(state: AgentState):
            """Check if thread needs compression and warn the agent."""
            if not thread:
                return {"messages": []}
            try:
                state_obj = thread.compression_state
                if state_obj.requires_compression:
                    msg_count = thread.messages.count()
                    warning = (
                        f"[SYSTEM] Your conversation has {msg_count} messages. "
                        f"Consider calling review_chunks() to manage context if it feels full."
                    )
                    return {"messages": [HumanMessage(content=warning)]}
            except Exception:
                pass
            return {"messages": []}

        def retriever(state: AgentState):
            if not self.has_rag:
                return

            retriever = self.get_history_aware_retriever()
            # Remove the initial instructions to prevent having two SystemMessages
            # This is necessary for compatibility with Anthropic
            messages_to_summarize = state["messages"][1:-1]
            input_message = state["messages"][-1]
            docs = retriever.invoke(
                {"input": input_message.content, "history": messages_to_summarize}
            )

            document_separator = self.get_document_separator()
            document_prompt = self.get_document_prompt()

            formatted_docs = document_separator.join(
                format_document(doc, document_prompt) for doc in docs
            )

            system_message = state["messages"][0]
            system_message.content += (
                f"\n\n---START OF CONTEXT---\n{formatted_docs}---END OF CONTEXT---\n\n"
            )

        def agent(state: AgentState):
            _logger = logging.getLogger("ai_assistant.agent")
            _logger.info(f"[NODE:agent] enter | messages_count={len(state['messages'])}")
            if _logger.isEnabledFor(logging.DEBUG):
                for i, msg in enumerate(state["messages"]):
                    _logger.debug(f"[AGENT INVOKE] msg[{i}] type={type(msg).__name__}: {str(msg.content)[:500]}")
            response = llm_with_tools.invoke(state["messages"])
            tc = getattr(response, 'tool_calls', [])
            _logger.info(f"[NODE:agent] exit | has_tool_calls={bool(tc)} tool_names={[t.get('name') for t in tc]} content_len={len(str(response.content)) if response.content else 0}")
            if thread:
                save_django_messages([response], thread=thread)
            return {"messages": [response]}

        def tool_selector(state: AgentState):
            last_message = state["messages"][-1]
            _logger = logging.getLogger("ai_assistant.agent")

            if not (isinstance(last_message, AIMessage) and last_message.tool_calls):
                _logger.info(f"[NODE:tool_selector] → continue (no tool_calls)")
                return "continue"

            tool_names = [tc.get("name") for tc in last_message.tool_calls]
            _logger.info(f"[NODE:tool_selector] evaluating | tools={tool_names}")

            # Guard A: stop after multiple WAITING_FOR_ASYNC results to prevent polling loops
            if self.stop_on_waiting_async:
                recent_tool_msgs = [
                    m for m in state["messages"][-10:]
                    if getattr(m, "type", None) == "tool"
                ]
                waiting_count = sum(
                    1 for m in recent_tool_msgs
                    if "WAITING_FOR_ASYNC" in str(m.content)
                )
                if waiting_count >= 2:
                    _logger.info(f"[NODE:tool_selector] → continue (guard A: {waiting_count} WAITING_FOR_ASYNC)")
                    return "continue"

            # Guard B: stop if the same tool is called repeatedly with no variation
            if self.max_consecutive_same_tool > 0:
                recent_ai_msgs = [
                    m for m in state["messages"][-( self.max_consecutive_same_tool * 2 + 2):]
                    if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)
                ]
                if len(recent_ai_msgs) >= self.max_consecutive_same_tool:
                    all_tool_names = [
                        tc["name"]
                        for m in recent_ai_msgs
                        for tc in (m.tool_calls or [])
                    ]
                    if (
                        len(all_tool_names) >= self.max_consecutive_same_tool
                        and len(set(all_tool_names[-self.max_consecutive_same_tool:])) == 1
                    ):
                        _logger.info(f"[NODE:tool_selector] → continue (guard B: repeated {all_tool_names[-self.max_consecutive_same_tool:]})")
                        return "continue"

            _logger.info(f"[NODE:tool_selector] → call_tool")
            return "call_tool"

        tools_by_name = {tool.name: tool for tool in tools}

        def prepare_tool_runs(state: AgentState):
            last_message = state["messages"][-1]
            if not isinstance(last_message, AIMessage):
                return {"pending_tool_calls": []}
            pending = list(last_message.tool_calls or [])
            _logger = logging.getLogger("ai_assistant.agent")
            _logger.info(f"[NODE:prepare_tool_runs] pending_count={len(pending)} names={[tc.get('name') for tc in pending]}")
            return {"pending_tool_calls": pending}

        def execute_tools(state: AgentState, config: RunnableConfig | None = None):
            """Execute pending tool calls as an explicit graph node with durable events."""
            import time as _time
            from apps.core.services import ExecutionService

            _et_logger = logging.getLogger("ai_assistant.agent")
            _et_start = _time.monotonic()
            pending = state.get("pending_tool_calls", [])
            _et_logger.info(f"[NODE:execute_tools] enter | pending_count={len(pending)}")

            tool_messages: list[ToolMessage] = []
            run_config = config or {}
            _et_logger.info(
                f"[NODE:execute_tools] config_received | config_type={type(config).__name__} "
                f"configurable.thread_id={run_config.get('configurable', {}).get('thread_id', 'MISSING') if isinstance(run_config, dict) else 'N/A'}"
            )
            graph_run_id = str(run_config.get("run_id") or "")
            graph = self._get_execution_graph()
            for tool_call in pending:
                tool_name = tool_call.get("name") or "unknown_tool"
                tool_args = tool_call.get("args") or {}
                tool_call_id = tool_call.get("id") or f"{tool_name}_call"
                node = None
                if graph is not None:
                    node = ExecutionService.start_node(
                        graph=graph,
                        name=tool_name,
                        kind="TOOL",
                        tool_call_id=tool_call_id,
                        input=tool_args,
                        metadata={"run_id": graph_run_id, "langgraph_node": "execute_tools"},
                    )
                    _et_logger.debug(
                        f"[DB-WRITE] ExecutionNode START | node_id={node.id} graph_id={node.graph_id} "
                        f"seq={node.sequence} tool={tool_name} call_id={tool_call_id} "
                        f"args_keys={list(tool_args.keys())}"
                    )

                tool = tools_by_name.get(tool_name)
                if tool is None:
                    error_message = f"Tool {tool_name!r} is not available."
                    _et_logger.warning(f"[NODE:execute_tools] tool_not_found | name={tool_name!r}")
                    if node is not None:
                        ExecutionService.fail_node(
                            node,
                            error={"error_type": "ToolNotFound"},
                            content=error_message,
                            payload={"tool_call_id": tool_call_id, "error_type": "ToolNotFound"},
                            reconcile_graph=False,
                        )
                        _et_logger.debug(
                            f"[DB-WRITE] ExecutionNode FAIL(ToolNotFound) | node_id={node.id} "
                            f"tool={tool_name} call_id={tool_call_id}"
                        )
                    tool_messages.append(
                        ToolMessage(content=error_message, tool_call_id=tool_call_id)
                    )
                    continue

                try:
                    self._current_execution_node = node
                    self._current_execution_node_id = node.id if node is not None else None
                    _t_start = _time.monotonic()
                    _et_logger.info(f"[NODE:execute_tools] invoking | name={tool_name} args_keys={list(tool_args.keys())}")
                    output = tool.invoke(tool_args, config=run_config)
                    _t_elapsed = _time.monotonic() - _t_start
                    _et_logger.info(f"[NODE:execute_tools] completed | name={tool_name} elapsed={_t_elapsed:.3f}s output_len={len(str(output))}")
                    _et_logger.debug(
                        f"[TOOL] invoked | name={tool_name} elapsed_ms={int(_t_elapsed * 1000)} "
                        f"output_len={len(str(output))} output_preview={str(output)[:500]!r}"
                    )
                    if node is not None:
                        node.refresh_from_db()
                    if node is not None and node.status == "WAITING":
                        ExecutionService.emit_event(
                            graph=graph,
                            node=node,
                            event_type="tool_dispatched",
                            status="WAITING",
                            content=str(output),
                            payload={"tool_call_id": tool_call_id, "output_preview": str(output)[:4000]},
                        )
                        _et_logger.debug(
                            f"[DB-WRITE] ExecutionEvent EMIT(tool_dispatched) | node_id={node.id} "
                            f"graph_id={graph.id} status=WAITING content_len={len(str(output))} "
                            f"call_id={tool_call_id}"
                        )
                    elif node is not None:
                        ExecutionService.complete_node(
                            node,
                            output={"preview": str(output)[:4000]},
                            content=str(output),
                            payload={"tool_call_id": tool_call_id, "output_preview": str(output)[:4000]},
                            reconcile_graph=False,
                        )
                        _et_logger.debug(
                            f"[DB-WRITE] ExecutionNode COMPLETE | node_id={node.id} status=SUCCEEDED "
                            f"seq={node.sequence} graph_id={node.graph_id} tool={tool_name} "
                            f"call_id={tool_call_id} output_preview={str(output)[:500]!r}"
                        )
                    tool_messages.append(
                        ToolMessage(content=str(output), tool_call_id=tool_call_id)
                    )
                    if thread:
                        _saved = save_django_messages(tool_messages[-1:], thread=thread)
                        _et_logger.debug(
                            f"[DB-WRITE] Message SAVED | thread_id={thread.id} role=tool_result "
                            f"msg_ids={[m.id for m in _saved]} tool_call_id={tool_call_id}"
                        )
                except Exception as exc:
                    error_message = f"{type(exc).__name__}: {exc}"
                    _et_logger.error(f"[NODE:execute_tools] failed | name={tool_name} error={error_message}", exc_info=True)
                    if node is not None:
                        ExecutionService.fail_node(
                            node,
                            error={"error_type": type(exc).__name__, "message": str(exc)},
                            content=error_message,
                            payload={"tool_call_id": tool_call_id, "error_type": type(exc).__name__},
                            reconcile_graph=False,
                        )
                        _et_logger.debug(
                            f"[DB-WRITE] ExecutionNode FAIL | node_id={node.id} status=FAILED "
                            f"seq={node.sequence} graph_id={node.graph_id} tool={tool_name} "
                            f"call_id={tool_call_id} error_type={type(exc).__name__} error_msg={str(exc)[:300]!r}"
                        )
                    tool_messages.append(
                        ToolMessage(content=error_message, tool_call_id=tool_call_id)
                    )
                    if thread:
                        _saved = save_django_messages(tool_messages[-1:], thread=thread)
                        _et_logger.debug(
                            f"[DB-WRITE] Message SAVED(error) | thread_id={thread.id} "
                            f"msg_ids={[m.id for m in _saved]} tool_call_id={tool_call_id} "
                            f"error={error_message[:200]!r}"
                        )
                finally:
                    self._current_execution_node = None
                    self._current_execution_node_id = None

            _et_elapsed = _time.monotonic() - _et_start
            _et_logger.info(f"[NODE:execute_tools] exit | tool_messages_count={len(tool_messages)} elapsed={_et_elapsed:.3f}s")
            return {"messages": tool_messages, "pending_tool_calls": []}

        def compress_tool_outputs(state: AgentState):
            """Compress large tool outputs before they reach the LLM."""
            _ct_logger = logging.getLogger("ai_assistant.agent")
            messages = state["messages"]
            last_tool_messages = []
            
            for msg in reversed(messages):
                if msg.type == "tool":
                    last_tool_messages.append(msg)
                else:
                    break
            
            if not last_tool_messages:
                _ct_logger.info(f"[NODE:compress_tool_outputs] skip (no tool messages)")
                return {"messages": []}

            _ct_logger.info(f"[NODE:compress_tool_outputs] enter | tool_msg_count={len(last_tool_messages)}")

            updated_messages = []
            for msg in last_tool_messages:
                content = str(msg.content)

                # Fix A: whitelist read_content_blob / save_long_content from Stage 1
                _whitelist_prefixes = ('=== ContentBlob #', '=== Focused Analysis for Blob #', '[Long Output Saved] blob_id=')
                if any(content.startswith(p) for p in _whitelist_prefixes):
                    updated_messages.append(msg)
                    continue

                # Fix B: raise threshold 2500 → 8000
                if len(content) > 8000:
                    try:
                        from apps.core.models.analyze.ContentBlob import ContentBlob
                        
                        summary = self._internal_generate_summary(content)
                        
                        blob = ContentBlob.objects.create(
                            raw_content=content,
                            content_size=len(content),
                            ai_summary=summary,
                            source_type="auto_hook",
                        )
                        
                        # Fix D: generate page_breakdown for structured pagination
                        if len(content) > 12000:
                            try:
                                pages = self._generate_page_breakdown(content)
                                if pages:
                                    blob.page_breakdown = pages
                                    blob.save(update_fields=['page_breakdown'])
                            except Exception as e:
                                logger.warning(f"Page breakdown generation skipped: {e}")
                        
                        # Replace content in the message object
                        new_content = (
                            f"⚠️ [AUTO-COMPRESSED] Tool output too large ({len(content)} chars). Moved to database.\n"
                            f"**Summary**: {summary}\n"
                            f"**Blob ID**: {blob.id}\n"
                        )
                        if blob.page_breakdown:
                            page_count = len(blob.page_breakdown)
                            new_content += (
                                f"**Pages**: {page_count} pages available.\n"
                                f"Use `read_content_blob(blob_id={blob.id}, page=N)` to read a specific page (1-{page_count}).\n"
                            )
                        else:
                            new_content += f"Use `read_content_blob(blob_id={blob.id})` for details."
                        msg.content = new_content
                        updated_messages.append(msg)
                    except Exception as e:
                        logger.error(f"Post-tool hook compression failed: {e}")
                else:
                    updated_messages.append(msg)
            
            # ── 截斷大型 ToolMessage，釋放 LLM context window ────────
            # 使用 compression_agent 輕量 LLM 產生摘要替換完整 tool output。
            # 保留 id（讓 add_messages reducer 替換舊訊息）和 tool_call_id（維持 tool_call→result 配對）。
            if thread:
                truncated_list = []
                for msg in updated_messages:
                    # Fix A (Stage 2): preserve whitelisted messages from Stage 2 truncation
                    _msg_content = str(msg.content)
                    _whitelist_prefixes = ('=== ContentBlob #', '=== Focused Analysis for Blob #', '[Long Output Saved] blob_id=')
                    _is_whitelisted = any(_msg_content.startswith(p) for p in _whitelist_prefixes)
                    if (
                        isinstance(msg, ToolMessage)
                        and len(_msg_content) > 300
                        and not _is_whitelisted
                    ):
                        _tool_name = getattr(msg, 'name', None) or 'tool'
                        try:
                            _summary = self._internal_generate_summary(
                                _msg_content, tool_name=_tool_name
                            )
                        except Exception:
                            _summary = _msg_content[:150] + "..."
                        truncated_list.append(
                            ToolMessage(
                                content=f"[{_tool_name}] {_summary}",
                                tool_call_id=msg.tool_call_id,
                                id=msg.id,
                            )
                        )
                    else:
                        truncated_list.append(msg)
                updated_messages = truncated_list

            # Return updated messages with same IDs to update state
            _ct_logger.info(f"[NODE:compress_tool_outputs] exit | updated_count={len(updated_messages)}")
            return {"messages": updated_messages}

        def record_response(state: AgentState):
            import time as _time
            from apps.core.services import ExecutionService

            _rr_logger = logging.getLogger("ai_assistant.agent")
            _rr_logger.info(f"[NODE:record_response] enter | messages_count={len(state['messages'])}")

            # Structured output must happen in the end, to avoid disabling tool calling.
            # Tool calling + structured output is not supported by OpenAI:
            if self.structured_output:
                messages = state["messages"]

                # Change the original system prompt:
                if isinstance(messages[0], SystemMessage):
                    messages[0].content += "\nUse the chat history to produce a JSON output."

                # Add a final message asking for JSON generation / structured output:
                json_request_message = HumanMessage(
                    content="Use the chat history to produce a JSON output."
                )
                messages.append(json_request_message)

                llm_with_structured_output = self.get_structured_output_llm()
                response = llm_with_structured_output.invoke(messages)
            else:
                response = state["messages"][-1].content

            if thread:
                thread_messages = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
                save_django_messages(cast(list[BaseMessage], thread_messages), thread=thread)
                _rr_logger.info(f"[NODE:record_response] saved {len(thread_messages)} messages to thread {thread.id}")
            graph = self._get_execution_graph()
            if graph is not None:
                graph.refresh_from_db(fields=["status"])
                if graph.status in ["RUNNING", "WAITING"]:
                    ExecutionService.complete_graph(graph, content=response)
                    _rr_logger.info(f"[NODE:record_response] completed graph {graph.id}")
            _rr_logger.info(f"[NODE:record_response] exit | output_len={len(str(response))}")
            return {"output": response}

        workflow = StateGraph(AgentState)

        workflow.add_node("setup", setup)
        workflow.add_node("history", history)
        workflow.add_node("context_check", context_check)
        workflow.add_node("retriever", retriever)
        workflow.add_node("agent", agent)
        workflow.add_node("prepare_tool_runs", prepare_tool_runs)
        workflow.add_node("execute_tools", execute_tools)
        workflow.add_node("compress_tool_outputs", compress_tool_outputs)
        workflow.add_node("respond", record_response)

        workflow.set_entry_point("setup")
        workflow.add_edge("setup", "history")
        workflow.add_edge("history", "context_check")
        workflow.add_edge("context_check", "retriever")
        workflow.add_edge("retriever", "agent")
        workflow.add_conditional_edges(
            "agent",
            tool_selector,
            {
                "call_tool": "prepare_tool_runs",
                "continue": "respond",
            },
        )
        workflow.add_edge("prepare_tool_runs", "execute_tools")
        workflow.add_edge("execute_tools", "compress_tool_outputs")
        workflow.add_edge("compress_tool_outputs", "agent")
        workflow.add_edge("respond", END)

        return workflow.compile()

    @overload
    def invoke(
        self,
        *args: Any,
        thread_id: Any | None,
        thread: Any | None = None,
        mode: Literal["invoke"] = "invoke",
        **kwargs: Any,
    ) -> dict:
        ...  # pragma: no cover

    @overload
    def invoke(
        self,
        *args: Any,
        thread_id: Any | None,
        thread: Any | None = None,
        mode: Literal["astream"],
        **kwargs: Any,
    ) -> AsyncIterator[dict]:
        ...  # pragma: no cover

    @with_cast_id
    def invoke(
        self,
        *args: Any,
        thread_id: Any | None = None,
        thread: Any | None = None,
        mode: Literal["invoke", "astream"] = "invoke",
        **kwargs: Any,
    ) -> dict | AsyncIterator[dict]:
        """Invoke the assistant LangChain graph with the given arguments and keyword arguments.\n
        This is the lower-level method to run the assistant.\n
        The graph is created by the `as_graph` method.\n

        If thread_id and thread are `None`, an in-memory chat message history is used.

        Args:
            *args: Positional arguments to pass to the graph.
                To add a new message, use a dict like `{"input": "user message"}`.
                If thread already has a `HumanMessage` in the end, you can invoke without args.
            thread_id (Any | None): The thread ID for the chat message history.
            thread (Any | None): The thread object for the chat message history.
            mode (invoke | astream): call named graph method
            **kwargs: Keyword arguments to pass to the graph.

        Returns:
            dict: The output of the assistant graph,
                 structured like `{"output": "assistant response", "history": ...}`.
        """
        config = kwargs.pop("config", {})
        from apps.core.services import ExecutionService

        config["max_concurrency"] = config.pop("max_concurrency", self.tool_max_concurrency)
        config["recursion_limit"] = config.pop("recursion_limit", getattr(self, "recursion_limit", 150))
        if thread is None and thread_id is not None:
            from apps.core.models import Thread

            thread = Thread.objects.filter(id=thread_id).first()
        execution_graph = ExecutionService.start_graph(
            thread=thread,
            assistant_id=getattr(self, "id", ""),
            title=getattr(self, "name", ""),
            metadata={"mode": mode},
        ) if thread is not None else None
        if execution_graph is not None:
            self._execution_graph = execution_graph
            self._current_execution_graph_id = execution_graph.id
            config.setdefault("configurable", {})["execution_graph_id"] = execution_graph.id
        # Keep an instance fallback for non-LangGraph tool invocation paths where
        # RunnableConfig may not be propagated into the wrapped tool function.
        self._current_invoke_thread_id = thread_id
        # 解析本 agent instance 對應的 overview_id / thread_id（供 ID 自動注入）
        self._set_auto_injected_ids()
        graph = self.as_graph(thread_id=thread_id, thread=thread)
        
        # Tool lifecycle persistence is graph-native. Callbacks remain available
        # for explicit opt-in integrations, but are no longer the primary event path.
        callbacks = self.get_callbacks()
        if callbacks:
            config.setdefault("callbacks", []).extend(callbacks)
        
        # Inject thread_id into configurable so nested agent tools can read caller_thread_id
        if thread_id is not None:
            config.setdefault("configurable", {})["thread_id"] = thread_id
        _logger = logging.getLogger("ai_assistant.agent")
        _logger.info(
            f"[INVOKE] agent={getattr(self, 'id', '?')} | thread_id={thread_id} | "
            f"configurable.thread_id={config.get('configurable', {}).get('thread_id')} | mode={mode}"
        )
        if mode not in ("invoke", "astream"):
            raise NotImplementedError(f"mode={mode!r}")
        try:
            return getattr(graph, mode)(*args, config=config, **kwargs)
        except GraphRecursionError as exc:
            # Agent 陷入迴圈或步驟過多（問題 ⑤）。回傳結構化「已達思考上限」訊息，
            # 而非讓例外傳播造成 Celery 無意義重試風暴。
            _logger.warning(
                f"[{getattr(self, 'id', '?')}] GraphRecursionError: hit recursion_limit="
                f"{config.get('recursion_limit')} (thread_id={thread_id})"
            )
            recursion_msg = (
                "⚠️ 已達思考步驟上限（GraphRecursionError）。"
                "可能原因：工具連續失敗導致重試、或任務本身需要過多步驟。"
                "請彙整目前已完成的進度，以結構化方式回報，並停止嘗試相同動作。"
            )
            if execution_graph is not None:
                ExecutionService.fail_graph(
                    execution_graph,
                    error=f"GraphRecursionError: hit limit {config.get('recursion_limit')}",
                    payload={
                        "error_type": "GraphRecursionError",
                        "recursion_limit": config.get("recursion_limit"),
                    },
                )
            # 回傳結構化結果而非拋出例外，避免上層 Celery 無意義重試
            return {"output": recursion_msg, "error": "GraphRecursionError"}
        except Exception as exc:
            if execution_graph is not None:
                ExecutionService.fail_graph(
                    execution_graph,
                    error=f"{type(exc).__name__}: {exc}",
                    payload={"error_type": type(exc).__name__},
                )
            raise

    @with_cast_id
    def run(self, message: str, thread_id: Any | None = None, **kwargs: Any) -> Any:
        """Run the assistant with the given message and thread ID.\n
        This is the higher-level method to run the assistant.\n

        Args:
            message (str): The user message to pass to the assistant.
            thread_id (Any | None): The thread ID for the chat message history.
                If `None`, an in-memory chat message history is used.
            **kwargs: Additional keyword arguments to pass to the graph.

        Returns:
            Any: The assistant response to the user message.
        """
        return self.invoke(
            {
                "input": message,
            },
            thread_id=thread_id,
            **kwargs,
        )["output"]

    @with_cast_id
    async def astream(
        self, message: str, thread: Any | None = None, **kwargs: Any
    ) -> AsyncIterable[Any]:
        """Async-stream the assistant with the given message and thread.\n
        This is the higher-level method to run the assistant.\n

        The graph runs inside an independent asyncio.Task so that it completes
        regardless of whether the SSE consumer (caller) is still iterating.

        Args:
            message (str): The user message to pass to the assistant.
            thread (Any | None): The thread object for the chat message history.
                If `None`, an in-memory chat message history is used.
            **kwargs: Additional keyword arguments to pass to the graph.

        Yields:
            Any: Token strings from the agent node.
        """
        import asyncio
        from asgiref.sync import sync_to_async

        queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
        _stream_logger = logging.getLogger("ai_assistant.agent")

        async def _run_graph_to_completion():
            try:
                graph_iter = await sync_to_async(self.invoke)(
                    {"input": message},
                    thread=thread,
                    thread_id=thread.id if thread else None,
                    mode="astream",
                    stream_mode="messages",
                    **kwargs,
                )
                token_count = 0
                async for output, metadata in graph_iter:
                    if metadata.get("langgraph_node") == "agent" and (content := output.content):
                        await queue.put(("token", content))
                        token_count += 1
                _stream_logger.info(f"[astream producer] graph completed | tokens_produced={token_count}")
                await queue.put(("done", None))
            except Exception as exc:
                _stream_logger.error(f"[astream producer] graph failed: {type(exc).__name__}: {exc}", exc_info=True)
                await queue.put(("error", exc))

        task = asyncio.create_task(_run_graph_to_completion())
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)
        _stream_logger.info(f"[astream] spawned background task={id(task)} thread={thread.id if thread else None}")

        try:
            while True:
                event_type, data = await queue.get()
                if event_type == "token":
                    yield data
                elif event_type == "done":
                    break
                elif event_type == "error":
                    raise data
        except GeneratorExit:
            _stream_logger.info("[astream consumer] GeneratorExit — SSE client disconnected; graph continues in background")
            raise

    def _run_as_tool(self, message: str, caller_thread_id: int | None = None, persistent: bool = True, **kwargs: Any) -> Any:
        _logger = logging.getLogger("ai_assistant.agent")
        _logger.info(f"[AS_TOOL CALLED] assistant_id={self.id!r} | message={message[:500]!r} | caller_thread_id={caller_thread_id} | persistent={persistent}")
        
        target_thread_id = None
        if caller_thread_id:
            try:
                from apps.core.models import Thread
                
                # 決定 Thread 名稱與隱藏屬性
                if persistent:
                    sub_thread_name = f"subagent_{self.id}_for_thread_{caller_thread_id}"
                    is_hidden = True
                else:
                    # 一次性調用也建立 DB 記錄以保證可靠性，但標記為隱藏
                    import uuid
                    sub_thread_name = f"ephemeral_{self.id}_{uuid.uuid4().hex[:8]}"
                    is_hidden = True
                
                # 繼承父層使用者
                parent_user = None
                try:
                    parent_thread = Thread.objects.filter(id=caller_thread_id).first()
                    if parent_thread:
                        parent_user = parent_thread.created_by
                except Exception:
                    pass

                sub_thread, created = Thread.objects.get_or_create(
                    name=sub_thread_name,
                    defaults={
                        'assistant_id': self.id, 
                        'created_by': parent_user,
                        'is_hidden': is_hidden
                    }
                )
                
                if not created:
                    if parent_user and not sub_thread.created_by:
                        sub_thread.created_by = parent_user
                    sub_thread.is_hidden = is_hidden
                    sub_thread.save(update_fields=['created_by', 'is_hidden'])

                target_thread_id = sub_thread.id
                # ── 同步更新 self._thread 以供 spawn_*_agent / get_callbacks 使用 ──
                # 沒有這行，AutomationAgent._thread 會一直是 None，
                # 導致 _get_caller_thread_id() 回傳 None，spawn 工具無法追蹤。
                if not getattr(self, '_thread', None):
                    self._thread = sub_thread
                _logger.info(f"[{self.id}] Binding to DB thread {sub_thread.id} (hidden={is_hidden}) for reliability.")
            except Exception as e:
                _logger.error(f"Failed to manage sub-thread: {e}")

        # 同步 caller_thread_id 到 agent instance（供 create_overview / notify_caller_agent 自動注入）
        if caller_thread_id:
            self._caller_thread_id = caller_thread_id
        if target_thread_id:
            self._current_invoke_thread_id = target_thread_id

        if target_thread_id:
            if persistent:
                # 不再對 LLM 暴露具體 Thread ID / parent_thread_id（問題 ②③），
                # 改為告知它「後端已自動處理 thread 關聯，工具呼叫時不必提供 thread_id/parent_thread_id」。
                message = f"[System Context: You are running as a managed sub-agent. Your Thread relationship (own thread + parent thread) has been automatically configured by the platform. When calling `create_overview` / `notify_caller_agent`, DO NOT pass thread_id or parent_thread_id — the backend auto-injects them. Once you decide the operation is complete, call `notify_caller_agent` to wake up your parent.]\n\n" + message
            else:
                message = f"[System Context: This is a ONE-TIME execution but state-managed for reliability. You are running in a managed Thread. Your output will be returned to the caller. Do not expect long-term interaction.]\n\n" + message
            
        return self.run(message, thread_id=target_thread_id, **kwargs)

    def as_tool(self, description: str) -> BaseTool:
        """Create a tool from the assistant.\n
        This is useful to compose assistants.\n

        Args:
            description (str): The description for the tool.

        Returns:
            BaseTool: A tool that runs the assistant. The tool name is this assistant's id.
        """
        _logger = logging.getLogger("ai_assistant.agent")
        _logger.info(f"[AS_TOOL REGISTERED] assistant_id={self.id!r} | description={description!r}")
        
        from langchain_core.runnables import RunnableConfig
        
        def _tool_func(message: str, persistent: bool = True, config: RunnableConfig = None) -> Any:
            thread_id = None
            if config and "configurable" in config:
                thread_id = config["configurable"].get("thread_id")
            # Fallback for non-LangGraph tool invocation paths where config is absent.
            if not thread_id:
                thread_id = getattr(self, '_current_invoke_thread_id', None)
            return self._run_as_tool(message, caller_thread_id=thread_id, persistent=persistent)

        return StructuredTool.from_function(
            func=_tool_func,
            name=self.id,
            description=description,
        )
