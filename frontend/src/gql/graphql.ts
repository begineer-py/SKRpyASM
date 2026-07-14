/* eslint-disable */
/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
/** Boolean expression to compare columns of type "Boolean". All fields are combined with logical 'AND'. */
export type Boolean_Comparison_Exp = {
  _eq?: boolean | null | undefined;
  _gt?: boolean | null | undefined;
  _gte?: boolean | null | undefined;
  _in?: Array<boolean> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: boolean | null | undefined;
  _lte?: boolean | null | undefined;
  _neq?: boolean | null | undefined;
  _nin?: Array<boolean> | null | undefined;
};

/** Boolean expression to compare columns of type "Int". All fields are combined with logical 'AND'. */
export type Int_Comparison_Exp = {
  _eq?: number | null | undefined;
  _gt?: number | null | undefined;
  _gte?: number | null | undefined;
  _in?: Array<number> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: number | null | undefined;
  _lte?: number | null | undefined;
  _neq?: number | null | undefined;
  _nin?: Array<number> | null | undefined;
};

/** Boolean expression to compare columns of type "String". All fields are combined with logical 'AND'. */
export type String_Comparison_Exp = {
  _eq?: string | null | undefined;
  _gt?: string | null | undefined;
  _gte?: string | null | undefined;
  /** does the column match the given case-insensitive pattern */
  _ilike?: string | null | undefined;
  _in?: Array<string> | null | undefined;
  /** does the column match the given POSIX regular expression, case insensitive */
  _iregex?: string | null | undefined;
  _is_null?: boolean | null | undefined;
  /** does the column match the given pattern */
  _like?: string | null | undefined;
  _lt?: string | null | undefined;
  _lte?: string | null | undefined;
  _neq?: string | null | undefined;
  /** does the column NOT match the given case-insensitive pattern */
  _nilike?: string | null | undefined;
  _nin?: Array<string> | null | undefined;
  /** does the column NOT match the given POSIX regular expression, case insensitive */
  _niregex?: string | null | undefined;
  /** does the column NOT match the given pattern */
  _nlike?: string | null | undefined;
  /** does the column NOT match the given POSIX regular expression, case sensitive */
  _nregex?: string | null | undefined;
  /** does the column NOT match the given SQL regular expression */
  _nsimilar?: string | null | undefined;
  /** does the column match the given POSIX regular expression, case sensitive */
  _regex?: string | null | undefined;
  /** does the column match the given SQL regular expression */
  _similar?: string | null | undefined;
};

/** Boolean expression to filter rows from the table "ai_assistant_globalcontextoverview". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Globalcontextoverview_Bool_Exp = {
  _and?: Array<Ai_Assistant_Globalcontextoverview_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Globalcontextoverview_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Globalcontextoverview_Bool_Exp> | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  attempted_exploits?: Jsonb_Comparison_Exp | null | undefined;
  confirmed_vulnerabilities?: Jsonb_Comparison_Exp | null | undefined;
  critical_artifacts?: Jsonb_Comparison_Exp | null | undefined;
  current_phase?: String_Comparison_Exp | null | undefined;
  excluded_paths?: Jsonb_Comparison_Exp | null | undefined;
  generated_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  metrics?: Jsonb_Comparison_Exp | null | undefined;
  mission?: String_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_globalcontextoverview" */
export type Ai_Assistant_Globalcontextoverview_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'ai_assistant_globalcontextoverview_pkey'
  /** unique or primary key constraint on columns "thread_id" */
  | 'ai_assistant_globalcontextoverview_thread_id_key';

/** input type for inserting data into table "ai_assistant_globalcontextoverview" */
export type Ai_Assistant_Globalcontextoverview_Insert_Input = {
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  attempted_exploits?: unknown;
  confirmed_vulnerabilities?: unknown;
  critical_artifacts?: unknown;
  current_phase?: string | null | undefined;
  excluded_paths?: unknown;
  generated_at?: unknown;
  id?: unknown;
  metrics?: unknown;
  mission?: string | null | undefined;
  thread_id?: unknown;
  updated_at?: unknown;
};

/** input type for inserting object relation for remote table "ai_assistant_globalcontextoverview" */
export type Ai_Assistant_Globalcontextoverview_Obj_Rel_Insert_Input = {
  data: Ai_Assistant_Globalcontextoverview_Insert_Input;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Globalcontextoverview_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_globalcontextoverview" */
export type Ai_Assistant_Globalcontextoverview_On_Conflict = {
  constraint: Ai_Assistant_Globalcontextoverview_Constraint;
  update_columns?: Array<Ai_Assistant_Globalcontextoverview_Update_Column>;
  where?: Ai_Assistant_Globalcontextoverview_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "ai_assistant_globalcontextoverview". */
export type Ai_Assistant_Globalcontextoverview_Order_By = {
  ai_assistant_thread?: Ai_Assistant_Thread_Order_By | null | undefined;
  attempted_exploits?: Order_By | null | undefined;
  confirmed_vulnerabilities?: Order_By | null | undefined;
  critical_artifacts?: Order_By | null | undefined;
  current_phase?: Order_By | null | undefined;
  excluded_paths?: Order_By | null | undefined;
  generated_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  metrics?: Order_By | null | undefined;
  mission?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** update columns of table "ai_assistant_globalcontextoverview" */
export type Ai_Assistant_Globalcontextoverview_Update_Column =
  /** column name */
  | 'attempted_exploits'
  /** column name */
  | 'confirmed_vulnerabilities'
  /** column name */
  | 'critical_artifacts'
  /** column name */
  | 'current_phase'
  /** column name */
  | 'excluded_paths'
  /** column name */
  | 'generated_at'
  /** column name */
  | 'id'
  /** column name */
  | 'metrics'
  /** column name */
  | 'mission'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'updated_at';

export type Ai_Assistant_Message_Aggregate_Bool_Exp = {
  bool_and?: Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Ai_Assistant_Message_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_And = {
  arguments: Ai_Assistant_Message_Select_Column_Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Message_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Ai_Assistant_Message_Select_Column_Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Message_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Ai_Assistant_Message_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Ai_Assistant_Message_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Message_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "ai_assistant_message" */
export type Ai_Assistant_Message_Aggregate_Order_By = {
  avg?: Ai_Assistant_Message_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Ai_Assistant_Message_Max_Order_By | null | undefined;
  min?: Ai_Assistant_Message_Min_Order_By | null | undefined;
  stddev?: Ai_Assistant_Message_Stddev_Order_By | null | undefined;
  stddev_pop?: Ai_Assistant_Message_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Ai_Assistant_Message_Stddev_Samp_Order_By | null | undefined;
  sum?: Ai_Assistant_Message_Sum_Order_By | null | undefined;
  var_pop?: Ai_Assistant_Message_Var_Pop_Order_By | null | undefined;
  var_samp?: Ai_Assistant_Message_Var_Samp_Order_By | null | undefined;
  variance?: Ai_Assistant_Message_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "ai_assistant_message" */
export type Ai_Assistant_Message_Arr_Rel_Insert_Input = {
  data: Array<Ai_Assistant_Message_Insert_Input>;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Message_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Avg_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "ai_assistant_message". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Message_Bool_Exp = {
  _and?: Array<Ai_Assistant_Message_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Message_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Message_Bool_Exp> | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_tooloutputlifecycle?: Ai_Assistant_Tooloutputlifecycle_Bool_Exp | null | undefined;
  compressed_content?: Jsonb_Comparison_Exp | null | undefined;
  compression_applied?: Boolean_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_tool_output?: Boolean_Comparison_Exp | null | undefined;
  message?: Jsonb_Comparison_Exp | null | undefined;
  role?: String_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_message" */
export type Ai_Assistant_Message_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'django_ai_assistant_message_pkey';

/** input type for inserting data into table "ai_assistant_message" */
export type Ai_Assistant_Message_Insert_Input = {
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  ai_assistant_tooloutputlifecycle?: Ai_Assistant_Tooloutputlifecycle_Obj_Rel_Insert_Input | null | undefined;
  compressed_content?: unknown;
  compression_applied?: boolean | null | undefined;
  created_at?: unknown;
  id?: unknown;
  is_tool_output?: boolean | null | undefined;
  message?: unknown;
  role?: string | null | undefined;
  thread_id?: unknown;
};

/** order by max() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  role?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  role?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "ai_assistant_message" */
export type Ai_Assistant_Message_Obj_Rel_Insert_Input = {
  data: Ai_Assistant_Message_Insert_Input;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Message_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_message" */
export type Ai_Assistant_Message_On_Conflict = {
  constraint: Ai_Assistant_Message_Constraint;
  update_columns?: Array<Ai_Assistant_Message_Update_Column>;
  where?: Ai_Assistant_Message_Bool_Exp | null | undefined;
};

/** select columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Select_Column =
  /** column name */
  | 'compressed_content'
  /** column name */
  | 'compression_applied'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_tool_output'
  /** column name */
  | 'message'
  /** column name */
  | 'role'
  /** column name */
  | 'thread_id';

/** select "ai_assistant_message_aggregate_bool_exp_bool_and_arguments_columns" columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Select_Column_Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'compression_applied'
  /** column name */
  | 'is_tool_output';

/** select "ai_assistant_message_aggregate_bool_exp_bool_or_arguments_columns" columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Select_Column_Ai_Assistant_Message_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'compression_applied'
  /** column name */
  | 'is_tool_output';

/** order by stddev() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Sum_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** update columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Update_Column =
  /** column name */
  | 'compressed_content'
  /** column name */
  | 'compression_applied'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_tool_output'
  /** column name */
  | 'message'
  /** column name */
  | 'role'
  /** column name */
  | 'thread_id';

/** order by var_pop() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "ai_assistant_message" */
export type Ai_Assistant_Message_Variance_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp = {
  avg?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Avg | null | undefined;
  corr?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr | null | undefined;
  count?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Count | null | undefined;
  covar_samp?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp | null | undefined;
  max?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Max | null | undefined;
  min?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Min | null | undefined;
  stddev_samp?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Stddev_Samp | null | undefined;
  sum?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Sum | null | undefined;
  var_samp?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Var_Samp | null | undefined;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Avg = {
  arguments: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Avg_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr = {
  arguments: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr_Arguments;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr_Arguments = {
  X: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr_Arguments_Columns;
  Y: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr_Arguments_Columns;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Ai_Assistant_Messagecompressionchunk_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp = {
  arguments: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp_Arguments;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp_Arguments = {
  X: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns;
  Y: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Max = {
  arguments: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Max_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Min = {
  arguments: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Min_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Stddev_Samp = {
  arguments: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Stddev_Samp_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Sum = {
  arguments: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Sum_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Var_Samp = {
  arguments: Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Var_Samp_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

/** order by aggregate values of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Aggregate_Order_By = {
  avg?: Ai_Assistant_Messagecompressionchunk_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Ai_Assistant_Messagecompressionchunk_Max_Order_By | null | undefined;
  min?: Ai_Assistant_Messagecompressionchunk_Min_Order_By | null | undefined;
  stddev?: Ai_Assistant_Messagecompressionchunk_Stddev_Order_By | null | undefined;
  stddev_pop?: Ai_Assistant_Messagecompressionchunk_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Ai_Assistant_Messagecompressionchunk_Stddev_Samp_Order_By | null | undefined;
  sum?: Ai_Assistant_Messagecompressionchunk_Sum_Order_By | null | undefined;
  var_pop?: Ai_Assistant_Messagecompressionchunk_Var_Pop_Order_By | null | undefined;
  var_samp?: Ai_Assistant_Messagecompressionchunk_Var_Samp_Order_By | null | undefined;
  variance?: Ai_Assistant_Messagecompressionchunk_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Arr_Rel_Insert_Input = {
  data: Array<Ai_Assistant_Messagecompressionchunk_Insert_Input>;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Messagecompressionchunk_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Avg_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "ai_assistant_messagecompressionchunk". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Messagecompressionchunk_Bool_Exp = {
  _and?: Array<Ai_Assistant_Messagecompressionchunk_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Messagecompressionchunk_Bool_Exp> | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  chunk_index?: Int_Comparison_Exp | null | undefined;
  compressed_content?: Jsonb_Comparison_Exp | null | undefined;
  compression_ratio?: Float8_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  end_message_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  original_content?: Jsonb_Comparison_Exp | null | undefined;
  start_message_id?: Bigint_Comparison_Exp | null | undefined;
  strategy?: String_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  tool_calls?: Jsonb_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Constraint =
  /** unique or primary key constraint on columns "thread_id", "chunk_index" */
  | 'ai_assistant_messagecomp_thread_id_chunk_index_77d15c9a_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'ai_assistant_messagecompressionchunk_pkey';

/** input type for inserting data into table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Insert_Input = {
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  chunk_index?: number | null | undefined;
  compressed_content?: unknown;
  compression_ratio?: unknown;
  created_at?: unknown;
  end_message_id?: unknown;
  id?: unknown;
  original_content?: unknown;
  start_message_id?: unknown;
  strategy?: string | null | undefined;
  thread_id?: unknown;
  tool_calls?: unknown;
  updated_at?: unknown;
};

/** order by max() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Max_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  strategy?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** order by min() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Min_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  strategy?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_On_Conflict = {
  constraint: Ai_Assistant_Messagecompressionchunk_Constraint;
  update_columns?: Array<Ai_Assistant_Messagecompressionchunk_Update_Column>;
  where?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
};

/** select columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column =
  /** column name */
  | 'chunk_index'
  /** column name */
  | 'compressed_content'
  /** column name */
  | 'compression_ratio'
  /** column name */
  | 'created_at'
  /** column name */
  | 'end_message_id'
  /** column name */
  | 'id'
  /** column name */
  | 'original_content'
  /** column name */
  | 'start_message_id'
  /** column name */
  | 'strategy'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'tool_calls'
  /** column name */
  | 'updated_at';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_avg_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Avg_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_corr_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Corr_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_covar_samp_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_max_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Max_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_min_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Min_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_stddev_samp_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Stddev_Samp_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_sum_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Sum_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** select "ai_assistant_messagecompressionchunk_aggregate_bool_exp_var_samp_arguments_columns" columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Select_Column_Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp_Var_Samp_Arguments_Columns =
  /** column name */
  | 'compression_ratio';

/** order by stddev() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Stddev_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Stddev_Pop_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Stddev_Samp_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Sum_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** update columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Update_Column =
  /** column name */
  | 'chunk_index'
  /** column name */
  | 'compressed_content'
  /** column name */
  | 'compression_ratio'
  /** column name */
  | 'created_at'
  /** column name */
  | 'end_message_id'
  /** column name */
  | 'id'
  /** column name */
  | 'original_content'
  /** column name */
  | 'start_message_id'
  /** column name */
  | 'strategy'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'tool_calls'
  /** column name */
  | 'updated_at';

/** order by var_pop() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Var_Pop_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Var_Samp_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "ai_assistant_messagecompressionchunk" */
export type Ai_Assistant_Messagecompressionchunk_Variance_Order_By = {
  chunk_index?: Order_By | null | undefined;
  compression_ratio?: Order_By | null | undefined;
  end_message_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  start_message_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

export type Ai_Assistant_Thread_Aggregate_Bool_Exp = {
  bool_and?: Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Ai_Assistant_Thread_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_And = {
  arguments: Ai_Assistant_Thread_Select_Column_Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Ai_Assistant_Thread_Select_Column_Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Ai_Assistant_Thread_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Ai_Assistant_Thread_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Aggregate_Order_By = {
  avg?: Ai_Assistant_Thread_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Ai_Assistant_Thread_Max_Order_By | null | undefined;
  min?: Ai_Assistant_Thread_Min_Order_By | null | undefined;
  stddev?: Ai_Assistant_Thread_Stddev_Order_By | null | undefined;
  stddev_pop?: Ai_Assistant_Thread_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Ai_Assistant_Thread_Stddev_Samp_Order_By | null | undefined;
  sum?: Ai_Assistant_Thread_Sum_Order_By | null | undefined;
  var_pop?: Ai_Assistant_Thread_Var_Pop_Order_By | null | undefined;
  var_samp?: Ai_Assistant_Thread_Var_Samp_Order_By | null | undefined;
  variance?: Ai_Assistant_Thread_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Arr_Rel_Insert_Input = {
  data: Array<Ai_Assistant_Thread_Insert_Input>;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Thread_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Avg_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "ai_assistant_thread". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Thread_Bool_Exp = {
  _and?: Array<Ai_Assistant_Thread_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Thread_Bool_Exp> | null | undefined;
  ai_assistant_globalcontextoverview?: Ai_Assistant_Globalcontextoverview_Bool_Exp | null | undefined;
  ai_assistant_messagecompressionchunks?: Ai_Assistant_Messagecompressionchunk_Bool_Exp | null | undefined;
  ai_assistant_messagecompressionchunks_aggregate?: Ai_Assistant_Messagecompressionchunk_Aggregate_Bool_Exp | null | undefined;
  ai_assistant_messages?: Ai_Assistant_Message_Bool_Exp | null | undefined;
  ai_assistant_messages_aggregate?: Ai_Assistant_Message_Aggregate_Bool_Exp | null | undefined;
  ai_assistant_thread_events?: Ai_Assistant_Thread_Event_Bool_Exp | null | undefined;
  ai_assistant_thread_events_aggregate?: Ai_Assistant_Thread_Event_Aggregate_Bool_Exp | null | undefined;
  ai_assistant_threadcompressionstate?: Ai_Assistant_Threadcompressionstate_Bool_Exp | null | undefined;
  assistant_id?: String_Comparison_Exp | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  bound_overview_id?: Bigint_Comparison_Exp | null | undefined;
  bound_target_id?: Bigint_Comparison_Exp | null | undefined;
  coreOverviewsByThreadId?: Core_Overview_Bool_Exp | null | undefined;
  coreOverviewsByThreadId_aggregate?: Core_Overview_Aggregate_Bool_Exp | null | undefined;
  coreSubagentDispatchesBySubThreadId?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  coreSubagentDispatchesBySubThreadId_aggregate?: Core_Subagent_Dispatch_Aggregate_Bool_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_overviews?: Core_Overview_Bool_Exp | null | undefined;
  core_overviews_aggregate?: Core_Overview_Aggregate_Bool_Exp | null | undefined;
  core_subagent_dispatches?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  core_subagent_dispatches_aggregate?: Core_Subagent_Dispatch_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  created_by_id?: Int_Comparison_Exp | null | undefined;
  execution_graphs?: Execution_Graph_Bool_Exp | null | undefined;
  execution_graphs_aggregate?: Execution_Graph_Aggregate_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_hidden?: Boolean_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'django_ai_assistant_thread_pkey';

export type Ai_Assistant_Thread_Event_Aggregate_Bool_Exp = {
  count?: Ai_Assistant_Thread_Event_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Ai_Assistant_Thread_Event_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Ai_Assistant_Thread_Event_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Ai_Assistant_Thread_Event_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Aggregate_Order_By = {
  avg?: Ai_Assistant_Thread_Event_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Ai_Assistant_Thread_Event_Max_Order_By | null | undefined;
  min?: Ai_Assistant_Thread_Event_Min_Order_By | null | undefined;
  stddev?: Ai_Assistant_Thread_Event_Stddev_Order_By | null | undefined;
  stddev_pop?: Ai_Assistant_Thread_Event_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Ai_Assistant_Thread_Event_Stddev_Samp_Order_By | null | undefined;
  sum?: Ai_Assistant_Thread_Event_Sum_Order_By | null | undefined;
  var_pop?: Ai_Assistant_Thread_Event_Var_Pop_Order_By | null | undefined;
  var_samp?: Ai_Assistant_Thread_Event_Var_Samp_Order_By | null | undefined;
  variance?: Ai_Assistant_Thread_Event_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Arr_Rel_Insert_Input = {
  data: Array<Ai_Assistant_Thread_Event_Insert_Input>;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Thread_Event_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Avg_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "ai_assistant_thread_event". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Thread_Event_Bool_Exp = {
  _and?: Array<Ai_Assistant_Thread_Event_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Thread_Event_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Thread_Event_Bool_Exp> | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  event_type?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  node_name?: String_Comparison_Exp | null | undefined;
  parent_run_id?: String_Comparison_Exp | null | undefined;
  payload?: Jsonb_Comparison_Exp | null | undefined;
  run_id?: String_Comparison_Exp | null | undefined;
  sequence?: Bigint_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  tool_name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'ai_assistant_thread_event_pkey';

/** input type for inserting data into table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Insert_Input = {
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  content?: string | null | undefined;
  created_at?: unknown;
  event_type?: string | null | undefined;
  id?: unknown;
  node_name?: string | null | undefined;
  parent_run_id?: string | null | undefined;
  payload?: unknown;
  run_id?: string | null | undefined;
  sequence?: unknown;
  status?: string | null | undefined;
  thread_id?: unknown;
  tool_name?: string | null | undefined;
};

/** order by max() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Max_Order_By = {
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  event_type?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  node_name?: Order_By | null | undefined;
  parent_run_id?: Order_By | null | undefined;
  run_id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  tool_name?: Order_By | null | undefined;
};

/** order by min() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Min_Order_By = {
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  event_type?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  node_name?: Order_By | null | undefined;
  parent_run_id?: Order_By | null | undefined;
  run_id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  tool_name?: Order_By | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_On_Conflict = {
  constraint: Ai_Assistant_Thread_Event_Constraint;
  update_columns?: Array<Ai_Assistant_Thread_Event_Update_Column>;
  where?: Ai_Assistant_Thread_Event_Bool_Exp | null | undefined;
};

/** select columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Select_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'event_type'
  /** column name */
  | 'id'
  /** column name */
  | 'node_name'
  /** column name */
  | 'parent_run_id'
  /** column name */
  | 'payload'
  /** column name */
  | 'run_id'
  /** column name */
  | 'sequence'
  /** column name */
  | 'status'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'tool_name';

/** order by stddev() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Sum_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** update columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'event_type'
  /** column name */
  | 'id'
  /** column name */
  | 'node_name'
  /** column name */
  | 'parent_run_id'
  /** column name */
  | 'payload'
  /** column name */
  | 'run_id'
  /** column name */
  | 'sequence'
  /** column name */
  | 'status'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'tool_name';

/** order by var_pop() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "ai_assistant_thread_event" */
export type Ai_Assistant_Thread_Event_Variance_Order_By = {
  id?: Order_By | null | undefined;
  sequence?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** input type for inserting data into table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Insert_Input = {
  ai_assistant_globalcontextoverview?: Ai_Assistant_Globalcontextoverview_Obj_Rel_Insert_Input | null | undefined;
  ai_assistant_messagecompressionchunks?: Ai_Assistant_Messagecompressionchunk_Arr_Rel_Insert_Input | null | undefined;
  ai_assistant_messages?: Ai_Assistant_Message_Arr_Rel_Insert_Input | null | undefined;
  ai_assistant_thread_events?: Ai_Assistant_Thread_Event_Arr_Rel_Insert_Input | null | undefined;
  ai_assistant_threadcompressionstate?: Ai_Assistant_Threadcompressionstate_Obj_Rel_Insert_Input | null | undefined;
  assistant_id?: string | null | undefined;
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  bound_overview_id?: unknown;
  bound_target_id?: unknown;
  coreOverviewsByThreadId?: Core_Overview_Arr_Rel_Insert_Input | null | undefined;
  coreSubagentDispatchesBySubThreadId?: Core_Subagent_Dispatch_Arr_Rel_Insert_Input | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_overviews?: Core_Overview_Arr_Rel_Insert_Input | null | undefined;
  core_subagent_dispatches?: Core_Subagent_Dispatch_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  created_by_id?: number | null | undefined;
  execution_graphs?: Execution_Graph_Arr_Rel_Insert_Input | null | undefined;
  id?: unknown;
  is_hidden?: boolean | null | undefined;
  name?: string | null | undefined;
  updated_at?: unknown;
};

/** order by max() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Max_Order_By = {
  assistant_id?: Order_By | null | undefined;
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** order by min() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Min_Order_By = {
  assistant_id?: Order_By | null | undefined;
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Obj_Rel_Insert_Input = {
  data: Ai_Assistant_Thread_Insert_Input;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Thread_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_thread" */
export type Ai_Assistant_Thread_On_Conflict = {
  constraint: Ai_Assistant_Thread_Constraint;
  update_columns?: Array<Ai_Assistant_Thread_Update_Column>;
  where?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "ai_assistant_thread". */
export type Ai_Assistant_Thread_Order_By = {
  ai_assistant_globalcontextoverview?: Ai_Assistant_Globalcontextoverview_Order_By | null | undefined;
  ai_assistant_messagecompressionchunks_aggregate?: Ai_Assistant_Messagecompressionchunk_Aggregate_Order_By | null | undefined;
  ai_assistant_messages_aggregate?: Ai_Assistant_Message_Aggregate_Order_By | null | undefined;
  ai_assistant_thread_events_aggregate?: Ai_Assistant_Thread_Event_Aggregate_Order_By | null | undefined;
  ai_assistant_threadcompressionstate?: Ai_Assistant_Threadcompressionstate_Order_By | null | undefined;
  assistant_id?: Order_By | null | undefined;
  auth_user?: Auth_User_Order_By | null | undefined;
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  coreOverviewsByThreadId_aggregate?: Core_Overview_Aggregate_Order_By | null | undefined;
  coreSubagentDispatchesBySubThreadId_aggregate?: Core_Subagent_Dispatch_Aggregate_Order_By | null | undefined;
  core_overview?: Core_Overview_Order_By | null | undefined;
  core_overviews_aggregate?: Core_Overview_Aggregate_Order_By | null | undefined;
  core_subagent_dispatches_aggregate?: Core_Subagent_Dispatch_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  execution_graphs_aggregate?: Execution_Graph_Aggregate_Order_By | null | undefined;
  id?: Order_By | null | undefined;
  is_hidden?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** select columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Select_Column =
  /** column name */
  | 'assistant_id'
  /** column name */
  | 'bound_overview_id'
  /** column name */
  | 'bound_target_id'
  /** column name */
  | 'created_at'
  /** column name */
  | 'created_by_id'
  /** column name */
  | 'id'
  /** column name */
  | 'is_hidden'
  /** column name */
  | 'name'
  /** column name */
  | 'updated_at';

/** select "ai_assistant_thread_aggregate_bool_exp_bool_and_arguments_columns" columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Select_Column_Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_hidden';

/** select "ai_assistant_thread_aggregate_bool_exp_bool_or_arguments_columns" columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Select_Column_Ai_Assistant_Thread_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_hidden';

/** order by stddev() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Stddev_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Stddev_Pop_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Stddev_Samp_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Sum_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** update columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Update_Column =
  /** column name */
  | 'assistant_id'
  /** column name */
  | 'bound_overview_id'
  /** column name */
  | 'bound_target_id'
  /** column name */
  | 'created_at'
  /** column name */
  | 'created_by_id'
  /** column name */
  | 'id'
  /** column name */
  | 'is_hidden'
  /** column name */
  | 'name'
  /** column name */
  | 'updated_at';

/** order by var_pop() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Var_Pop_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Var_Samp_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "ai_assistant_thread" */
export type Ai_Assistant_Thread_Variance_Order_By = {
  bound_overview_id?: Order_By | null | undefined;
  bound_target_id?: Order_By | null | undefined;
  created_by_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "ai_assistant_threadcompressionstate". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Threadcompressionstate_Bool_Exp = {
  _and?: Array<Ai_Assistant_Threadcompressionstate_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Threadcompressionstate_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Threadcompressionstate_Bool_Exp> | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  compression_summary?: Jsonb_Comparison_Exp | null | undefined;
  context_window_used_tokens?: Int_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  last_compressed_at?: Timestamptz_Comparison_Exp | null | undefined;
  last_compressed_message_id?: Bigint_Comparison_Exp | null | undefined;
  requires_compression?: Boolean_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  total_message_count?: Int_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_threadcompressionstate" */
export type Ai_Assistant_Threadcompressionstate_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'ai_assistant_threadcompressionstate_pkey'
  /** unique or primary key constraint on columns "thread_id" */
  | 'ai_assistant_threadcompressionstate_thread_id_key';

/** input type for inserting data into table "ai_assistant_threadcompressionstate" */
export type Ai_Assistant_Threadcompressionstate_Insert_Input = {
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  compression_summary?: unknown;
  context_window_used_tokens?: number | null | undefined;
  created_at?: unknown;
  id?: unknown;
  last_compressed_at?: unknown;
  last_compressed_message_id?: unknown;
  requires_compression?: boolean | null | undefined;
  thread_id?: unknown;
  total_message_count?: number | null | undefined;
  updated_at?: unknown;
};

/** input type for inserting object relation for remote table "ai_assistant_threadcompressionstate" */
export type Ai_Assistant_Threadcompressionstate_Obj_Rel_Insert_Input = {
  data: Ai_Assistant_Threadcompressionstate_Insert_Input;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Threadcompressionstate_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_threadcompressionstate" */
export type Ai_Assistant_Threadcompressionstate_On_Conflict = {
  constraint: Ai_Assistant_Threadcompressionstate_Constraint;
  update_columns?: Array<Ai_Assistant_Threadcompressionstate_Update_Column>;
  where?: Ai_Assistant_Threadcompressionstate_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "ai_assistant_threadcompressionstate". */
export type Ai_Assistant_Threadcompressionstate_Order_By = {
  ai_assistant_thread?: Ai_Assistant_Thread_Order_By | null | undefined;
  compression_summary?: Order_By | null | undefined;
  context_window_used_tokens?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_compressed_at?: Order_By | null | undefined;
  last_compressed_message_id?: Order_By | null | undefined;
  requires_compression?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  total_message_count?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** update columns of table "ai_assistant_threadcompressionstate" */
export type Ai_Assistant_Threadcompressionstate_Update_Column =
  /** column name */
  | 'compression_summary'
  /** column name */
  | 'context_window_used_tokens'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'last_compressed_at'
  /** column name */
  | 'last_compressed_message_id'
  /** column name */
  | 'requires_compression'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'total_message_count'
  /** column name */
  | 'updated_at';

/** Boolean expression to filter rows from the table "ai_assistant_tooloutputlifecycle". All fields are combined with a logical 'AND'. */
export type Ai_Assistant_Tooloutputlifecycle_Bool_Exp = {
  _and?: Array<Ai_Assistant_Tooloutputlifecycle_Bool_Exp> | null | undefined;
  _not?: Ai_Assistant_Tooloutputlifecycle_Bool_Exp | null | undefined;
  _or?: Array<Ai_Assistant_Tooloutputlifecycle_Bool_Exp> | null | undefined;
  ai_assistant_message?: Ai_Assistant_Message_Bool_Exp | null | undefined;
  compressed_output?: String_Comparison_Exp | null | undefined;
  compressed_size?: Int_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  message_id?: Bigint_Comparison_Exp | null | undefined;
  original_output_size?: Int_Comparison_Exp | null | undefined;
  reason?: String_Comparison_Exp | null | undefined;
  strategy?: String_Comparison_Exp | null | undefined;
  tool_name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "ai_assistant_tooloutputlifecycle" */
export type Ai_Assistant_Tooloutputlifecycle_Constraint =
  /** unique or primary key constraint on columns "message_id" */
  | 'ai_assistant_tooloutputlifecycle_message_id_key'
  /** unique or primary key constraint on columns "id" */
  | 'ai_assistant_tooloutputlifecycle_pkey';

/** input type for inserting data into table "ai_assistant_tooloutputlifecycle" */
export type Ai_Assistant_Tooloutputlifecycle_Insert_Input = {
  ai_assistant_message?: Ai_Assistant_Message_Obj_Rel_Insert_Input | null | undefined;
  compressed_output?: string | null | undefined;
  compressed_size?: number | null | undefined;
  created_at?: unknown;
  id?: unknown;
  message_id?: unknown;
  original_output_size?: number | null | undefined;
  reason?: string | null | undefined;
  strategy?: string | null | undefined;
  tool_name?: string | null | undefined;
};

/** input type for inserting object relation for remote table "ai_assistant_tooloutputlifecycle" */
export type Ai_Assistant_Tooloutputlifecycle_Obj_Rel_Insert_Input = {
  data: Ai_Assistant_Tooloutputlifecycle_Insert_Input;
  /** upsert condition */
  on_conflict?: Ai_Assistant_Tooloutputlifecycle_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "ai_assistant_tooloutputlifecycle" */
export type Ai_Assistant_Tooloutputlifecycle_On_Conflict = {
  constraint: Ai_Assistant_Tooloutputlifecycle_Constraint;
  update_columns?: Array<Ai_Assistant_Tooloutputlifecycle_Update_Column>;
  where?: Ai_Assistant_Tooloutputlifecycle_Bool_Exp | null | undefined;
};

/** update columns of table "ai_assistant_tooloutputlifecycle" */
export type Ai_Assistant_Tooloutputlifecycle_Update_Column =
  /** column name */
  | 'compressed_output'
  /** column name */
  | 'compressed_size'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'message_id'
  /** column name */
  | 'original_output_size'
  /** column name */
  | 'reason'
  /** column name */
  | 'strategy'
  /** column name */
  | 'tool_name';

/** Boolean expression to filter rows from the table "auth_group". All fields are combined with a logical 'AND'. */
export type Auth_Group_Bool_Exp = {
  _and?: Array<Auth_Group_Bool_Exp> | null | undefined;
  _not?: Auth_Group_Bool_Exp | null | undefined;
  _or?: Array<Auth_Group_Bool_Exp> | null | undefined;
  auth_group_permissions?: Auth_Group_Permissions_Bool_Exp | null | undefined;
  auth_group_permissions_aggregate?: Auth_Group_Permissions_Aggregate_Bool_Exp | null | undefined;
  auth_user_groups?: Auth_User_Groups_Bool_Exp | null | undefined;
  auth_user_groups_aggregate?: Auth_User_Groups_Aggregate_Bool_Exp | null | undefined;
  id?: Int_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "auth_group" */
export type Auth_Group_Constraint =
  /** unique or primary key constraint on columns "name" */
  | 'auth_group_name_key'
  /** unique or primary key constraint on columns "id" */
  | 'auth_group_pkey';

/** input type for inserting data into table "auth_group" */
export type Auth_Group_Insert_Input = {
  auth_group_permissions?: Auth_Group_Permissions_Arr_Rel_Insert_Input | null | undefined;
  auth_user_groups?: Auth_User_Groups_Arr_Rel_Insert_Input | null | undefined;
  id?: number | null | undefined;
  name?: string | null | undefined;
};

/** input type for inserting object relation for remote table "auth_group" */
export type Auth_Group_Obj_Rel_Insert_Input = {
  data: Auth_Group_Insert_Input;
  /** upsert condition */
  on_conflict?: Auth_Group_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "auth_group" */
export type Auth_Group_On_Conflict = {
  constraint: Auth_Group_Constraint;
  update_columns?: Array<Auth_Group_Update_Column>;
  where?: Auth_Group_Bool_Exp | null | undefined;
};

export type Auth_Group_Permissions_Aggregate_Bool_Exp = {
  count?: Auth_Group_Permissions_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Auth_Group_Permissions_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Auth_Group_Permissions_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Auth_Group_Permissions_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "auth_group_permissions" */
export type Auth_Group_Permissions_Arr_Rel_Insert_Input = {
  data: Array<Auth_Group_Permissions_Insert_Input>;
  /** upsert condition */
  on_conflict?: Auth_Group_Permissions_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "auth_group_permissions". All fields are combined with a logical 'AND'. */
export type Auth_Group_Permissions_Bool_Exp = {
  _and?: Array<Auth_Group_Permissions_Bool_Exp> | null | undefined;
  _not?: Auth_Group_Permissions_Bool_Exp | null | undefined;
  _or?: Array<Auth_Group_Permissions_Bool_Exp> | null | undefined;
  auth_group?: Auth_Group_Bool_Exp | null | undefined;
  auth_permission?: Auth_Permission_Bool_Exp | null | undefined;
  group_id?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  permission_id?: Int_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "auth_group_permissions" */
export type Auth_Group_Permissions_Constraint =
  /** unique or primary key constraint on columns "permission_id", "group_id" */
  | 'auth_group_permissions_group_id_permission_id_0cd325b0_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'auth_group_permissions_pkey';

/** input type for inserting data into table "auth_group_permissions" */
export type Auth_Group_Permissions_Insert_Input = {
  auth_group?: Auth_Group_Obj_Rel_Insert_Input | null | undefined;
  auth_permission?: Auth_Permission_Obj_Rel_Insert_Input | null | undefined;
  group_id?: number | null | undefined;
  id?: unknown;
  permission_id?: number | null | undefined;
};

/** on_conflict condition type for table "auth_group_permissions" */
export type Auth_Group_Permissions_On_Conflict = {
  constraint: Auth_Group_Permissions_Constraint;
  update_columns?: Array<Auth_Group_Permissions_Update_Column>;
  where?: Auth_Group_Permissions_Bool_Exp | null | undefined;
};

/** select columns of table "auth_group_permissions" */
export type Auth_Group_Permissions_Select_Column =
  /** column name */
  | 'group_id'
  /** column name */
  | 'id'
  /** column name */
  | 'permission_id';

/** update columns of table "auth_group_permissions" */
export type Auth_Group_Permissions_Update_Column =
  /** column name */
  | 'group_id'
  /** column name */
  | 'id'
  /** column name */
  | 'permission_id';

/** update columns of table "auth_group" */
export type Auth_Group_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'name';

export type Auth_Permission_Aggregate_Bool_Exp = {
  count?: Auth_Permission_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Auth_Permission_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Auth_Permission_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Auth_Permission_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "auth_permission" */
export type Auth_Permission_Arr_Rel_Insert_Input = {
  data: Array<Auth_Permission_Insert_Input>;
  /** upsert condition */
  on_conflict?: Auth_Permission_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "auth_permission". All fields are combined with a logical 'AND'. */
export type Auth_Permission_Bool_Exp = {
  _and?: Array<Auth_Permission_Bool_Exp> | null | undefined;
  _not?: Auth_Permission_Bool_Exp | null | undefined;
  _or?: Array<Auth_Permission_Bool_Exp> | null | undefined;
  auth_group_permissions?: Auth_Group_Permissions_Bool_Exp | null | undefined;
  auth_group_permissions_aggregate?: Auth_Group_Permissions_Aggregate_Bool_Exp | null | undefined;
  auth_user_user_permissions?: Auth_User_User_Permissions_Bool_Exp | null | undefined;
  auth_user_user_permissions_aggregate?: Auth_User_User_Permissions_Aggregate_Bool_Exp | null | undefined;
  codename?: String_Comparison_Exp | null | undefined;
  content_type_id?: Int_Comparison_Exp | null | undefined;
  django_content_type?: Django_Content_Type_Bool_Exp | null | undefined;
  id?: Int_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "auth_permission" */
export type Auth_Permission_Constraint =
  /** unique or primary key constraint on columns "codename", "content_type_id" */
  | 'auth_permission_content_type_id_codename_01ab375a_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'auth_permission_pkey';

/** input type for inserting data into table "auth_permission" */
export type Auth_Permission_Insert_Input = {
  auth_group_permissions?: Auth_Group_Permissions_Arr_Rel_Insert_Input | null | undefined;
  auth_user_user_permissions?: Auth_User_User_Permissions_Arr_Rel_Insert_Input | null | undefined;
  codename?: string | null | undefined;
  content_type_id?: number | null | undefined;
  django_content_type?: Django_Content_Type_Obj_Rel_Insert_Input | null | undefined;
  id?: number | null | undefined;
  name?: string | null | undefined;
};

/** input type for inserting object relation for remote table "auth_permission" */
export type Auth_Permission_Obj_Rel_Insert_Input = {
  data: Auth_Permission_Insert_Input;
  /** upsert condition */
  on_conflict?: Auth_Permission_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "auth_permission" */
export type Auth_Permission_On_Conflict = {
  constraint: Auth_Permission_Constraint;
  update_columns?: Array<Auth_Permission_Update_Column>;
  where?: Auth_Permission_Bool_Exp | null | undefined;
};

/** select columns of table "auth_permission" */
export type Auth_Permission_Select_Column =
  /** column name */
  | 'codename'
  /** column name */
  | 'content_type_id'
  /** column name */
  | 'id'
  /** column name */
  | 'name';

/** update columns of table "auth_permission" */
export type Auth_Permission_Update_Column =
  /** column name */
  | 'codename'
  /** column name */
  | 'content_type_id'
  /** column name */
  | 'id'
  /** column name */
  | 'name';

/** Boolean expression to filter rows from the table "auth_user". All fields are combined with a logical 'AND'. */
export type Auth_User_Bool_Exp = {
  _and?: Array<Auth_User_Bool_Exp> | null | undefined;
  _not?: Auth_User_Bool_Exp | null | undefined;
  _or?: Array<Auth_User_Bool_Exp> | null | undefined;
  ai_assistant_threads?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_threads_aggregate?: Ai_Assistant_Thread_Aggregate_Bool_Exp | null | undefined;
  auth_user_groups?: Auth_User_Groups_Bool_Exp | null | undefined;
  auth_user_groups_aggregate?: Auth_User_Groups_Aggregate_Bool_Exp | null | undefined;
  auth_user_user_permissions?: Auth_User_User_Permissions_Bool_Exp | null | undefined;
  auth_user_user_permissions_aggregate?: Auth_User_User_Permissions_Aggregate_Bool_Exp | null | undefined;
  authtoken_token?: Authtoken_Token_Bool_Exp | null | undefined;
  core_historicalips?: Core_Historicalip_Bool_Exp | null | undefined;
  core_historicalips_aggregate?: Core_Historicalip_Aggregate_Bool_Exp | null | undefined;
  core_historicalports?: Core_Historicalport_Bool_Exp | null | undefined;
  core_historicalports_aggregate?: Core_Historicalport_Aggregate_Bool_Exp | null | undefined;
  core_historicalsubdomains?: Core_Historicalsubdomain_Bool_Exp | null | undefined;
  core_historicalsubdomains_aggregate?: Core_Historicalsubdomain_Aggregate_Bool_Exp | null | undefined;
  core_historicalurlresults?: Core_Historicalurlresult_Bool_Exp | null | undefined;
  core_historicalurlresults_aggregate?: Core_Historicalurlresult_Aggregate_Bool_Exp | null | undefined;
  date_joined?: Timestamptz_Comparison_Exp | null | undefined;
  django_admin_logs?: Django_Admin_Log_Bool_Exp | null | undefined;
  django_admin_logs_aggregate?: Django_Admin_Log_Aggregate_Bool_Exp | null | undefined;
  email?: String_Comparison_Exp | null | undefined;
  first_name?: String_Comparison_Exp | null | undefined;
  id?: Int_Comparison_Exp | null | undefined;
  is_active?: Boolean_Comparison_Exp | null | undefined;
  is_staff?: Boolean_Comparison_Exp | null | undefined;
  is_superuser?: Boolean_Comparison_Exp | null | undefined;
  last_login?: Timestamptz_Comparison_Exp | null | undefined;
  last_name?: String_Comparison_Exp | null | undefined;
  password?: String_Comparison_Exp | null | undefined;
  username?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "auth_user" */
export type Auth_User_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'auth_user_pkey'
  /** unique or primary key constraint on columns "username" */
  | 'auth_user_username_key';

export type Auth_User_Groups_Aggregate_Bool_Exp = {
  count?: Auth_User_Groups_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Auth_User_Groups_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Auth_User_Groups_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Auth_User_Groups_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "auth_user_groups" */
export type Auth_User_Groups_Aggregate_Order_By = {
  avg?: Auth_User_Groups_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Auth_User_Groups_Max_Order_By | null | undefined;
  min?: Auth_User_Groups_Min_Order_By | null | undefined;
  stddev?: Auth_User_Groups_Stddev_Order_By | null | undefined;
  stddev_pop?: Auth_User_Groups_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Auth_User_Groups_Stddev_Samp_Order_By | null | undefined;
  sum?: Auth_User_Groups_Sum_Order_By | null | undefined;
  var_pop?: Auth_User_Groups_Var_Pop_Order_By | null | undefined;
  var_samp?: Auth_User_Groups_Var_Samp_Order_By | null | undefined;
  variance?: Auth_User_Groups_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "auth_user_groups" */
export type Auth_User_Groups_Arr_Rel_Insert_Input = {
  data: Array<Auth_User_Groups_Insert_Input>;
  /** upsert condition */
  on_conflict?: Auth_User_Groups_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Avg_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "auth_user_groups". All fields are combined with a logical 'AND'. */
export type Auth_User_Groups_Bool_Exp = {
  _and?: Array<Auth_User_Groups_Bool_Exp> | null | undefined;
  _not?: Auth_User_Groups_Bool_Exp | null | undefined;
  _or?: Array<Auth_User_Groups_Bool_Exp> | null | undefined;
  auth_group?: Auth_Group_Bool_Exp | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  group_id?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  user_id?: Int_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "auth_user_groups" */
export type Auth_User_Groups_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'auth_user_groups_pkey'
  /** unique or primary key constraint on columns "user_id", "group_id" */
  | 'auth_user_groups_user_id_group_id_94350c0c_uniq';

/** input type for inserting data into table "auth_user_groups" */
export type Auth_User_Groups_Insert_Input = {
  auth_group?: Auth_Group_Obj_Rel_Insert_Input | null | undefined;
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  group_id?: number | null | undefined;
  id?: unknown;
  user_id?: number | null | undefined;
};

/** order by max() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Max_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Min_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "auth_user_groups" */
export type Auth_User_Groups_On_Conflict = {
  constraint: Auth_User_Groups_Constraint;
  update_columns?: Array<Auth_User_Groups_Update_Column>;
  where?: Auth_User_Groups_Bool_Exp | null | undefined;
};

/** select columns of table "auth_user_groups" */
export type Auth_User_Groups_Select_Column =
  /** column name */
  | 'group_id'
  /** column name */
  | 'id'
  /** column name */
  | 'user_id';

/** order by stddev() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Stddev_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Stddev_Pop_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Stddev_Samp_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Sum_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** update columns of table "auth_user_groups" */
export type Auth_User_Groups_Update_Column =
  /** column name */
  | 'group_id'
  /** column name */
  | 'id'
  /** column name */
  | 'user_id';

/** order by var_pop() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Var_Pop_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Var_Samp_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "auth_user_groups" */
export type Auth_User_Groups_Variance_Order_By = {
  group_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** input type for inserting data into table "auth_user" */
export type Auth_User_Insert_Input = {
  ai_assistant_threads?: Ai_Assistant_Thread_Arr_Rel_Insert_Input | null | undefined;
  auth_user_groups?: Auth_User_Groups_Arr_Rel_Insert_Input | null | undefined;
  auth_user_user_permissions?: Auth_User_User_Permissions_Arr_Rel_Insert_Input | null | undefined;
  authtoken_token?: Authtoken_Token_Obj_Rel_Insert_Input | null | undefined;
  core_historicalips?: Core_Historicalip_Arr_Rel_Insert_Input | null | undefined;
  core_historicalports?: Core_Historicalport_Arr_Rel_Insert_Input | null | undefined;
  core_historicalsubdomains?: Core_Historicalsubdomain_Arr_Rel_Insert_Input | null | undefined;
  core_historicalurlresults?: Core_Historicalurlresult_Arr_Rel_Insert_Input | null | undefined;
  date_joined?: unknown;
  django_admin_logs?: Django_Admin_Log_Arr_Rel_Insert_Input | null | undefined;
  email?: string | null | undefined;
  first_name?: string | null | undefined;
  id?: number | null | undefined;
  is_active?: boolean | null | undefined;
  is_staff?: boolean | null | undefined;
  is_superuser?: boolean | null | undefined;
  last_login?: unknown;
  last_name?: string | null | undefined;
  password?: string | null | undefined;
  username?: string | null | undefined;
};

/** input type for inserting object relation for remote table "auth_user" */
export type Auth_User_Obj_Rel_Insert_Input = {
  data: Auth_User_Insert_Input;
  /** upsert condition */
  on_conflict?: Auth_User_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "auth_user" */
export type Auth_User_On_Conflict = {
  constraint: Auth_User_Constraint;
  update_columns?: Array<Auth_User_Update_Column>;
  where?: Auth_User_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "auth_user". */
export type Auth_User_Order_By = {
  ai_assistant_threads_aggregate?: Ai_Assistant_Thread_Aggregate_Order_By | null | undefined;
  auth_user_groups_aggregate?: Auth_User_Groups_Aggregate_Order_By | null | undefined;
  auth_user_user_permissions_aggregate?: Auth_User_User_Permissions_Aggregate_Order_By | null | undefined;
  authtoken_token?: Authtoken_Token_Order_By | null | undefined;
  core_historicalips_aggregate?: Core_Historicalip_Aggregate_Order_By | null | undefined;
  core_historicalports_aggregate?: Core_Historicalport_Aggregate_Order_By | null | undefined;
  core_historicalsubdomains_aggregate?: Core_Historicalsubdomain_Aggregate_Order_By | null | undefined;
  core_historicalurlresults_aggregate?: Core_Historicalurlresult_Aggregate_Order_By | null | undefined;
  date_joined?: Order_By | null | undefined;
  django_admin_logs_aggregate?: Django_Admin_Log_Aggregate_Order_By | null | undefined;
  email?: Order_By | null | undefined;
  first_name?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  is_active?: Order_By | null | undefined;
  is_staff?: Order_By | null | undefined;
  is_superuser?: Order_By | null | undefined;
  last_login?: Order_By | null | undefined;
  last_name?: Order_By | null | undefined;
  password?: Order_By | null | undefined;
  username?: Order_By | null | undefined;
};

/** update columns of table "auth_user" */
export type Auth_User_Update_Column =
  /** column name */
  | 'date_joined'
  /** column name */
  | 'email'
  /** column name */
  | 'first_name'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_staff'
  /** column name */
  | 'is_superuser'
  /** column name */
  | 'last_login'
  /** column name */
  | 'last_name'
  /** column name */
  | 'password'
  /** column name */
  | 'username';

export type Auth_User_User_Permissions_Aggregate_Bool_Exp = {
  count?: Auth_User_User_Permissions_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Auth_User_User_Permissions_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Auth_User_User_Permissions_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Auth_User_User_Permissions_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Aggregate_Order_By = {
  avg?: Auth_User_User_Permissions_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Auth_User_User_Permissions_Max_Order_By | null | undefined;
  min?: Auth_User_User_Permissions_Min_Order_By | null | undefined;
  stddev?: Auth_User_User_Permissions_Stddev_Order_By | null | undefined;
  stddev_pop?: Auth_User_User_Permissions_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Auth_User_User_Permissions_Stddev_Samp_Order_By | null | undefined;
  sum?: Auth_User_User_Permissions_Sum_Order_By | null | undefined;
  var_pop?: Auth_User_User_Permissions_Var_Pop_Order_By | null | undefined;
  var_samp?: Auth_User_User_Permissions_Var_Samp_Order_By | null | undefined;
  variance?: Auth_User_User_Permissions_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Arr_Rel_Insert_Input = {
  data: Array<Auth_User_User_Permissions_Insert_Input>;
  /** upsert condition */
  on_conflict?: Auth_User_User_Permissions_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Avg_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "auth_user_user_permissions". All fields are combined with a logical 'AND'. */
export type Auth_User_User_Permissions_Bool_Exp = {
  _and?: Array<Auth_User_User_Permissions_Bool_Exp> | null | undefined;
  _not?: Auth_User_User_Permissions_Bool_Exp | null | undefined;
  _or?: Array<Auth_User_User_Permissions_Bool_Exp> | null | undefined;
  auth_permission?: Auth_Permission_Bool_Exp | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  permission_id?: Int_Comparison_Exp | null | undefined;
  user_id?: Int_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'auth_user_user_permissions_pkey'
  /** unique or primary key constraint on columns "permission_id", "user_id" */
  | 'auth_user_user_permissions_user_id_permission_id_14a6b632_uniq';

/** input type for inserting data into table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Insert_Input = {
  auth_permission?: Auth_Permission_Obj_Rel_Insert_Input | null | undefined;
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  permission_id?: number | null | undefined;
  user_id?: number | null | undefined;
};

/** order by max() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Max_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Min_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_On_Conflict = {
  constraint: Auth_User_User_Permissions_Constraint;
  update_columns?: Array<Auth_User_User_Permissions_Update_Column>;
  where?: Auth_User_User_Permissions_Bool_Exp | null | undefined;
};

/** select columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'permission_id'
  /** column name */
  | 'user_id';

/** order by stddev() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Sum_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** update columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'permission_id'
  /** column name */
  | 'user_id';

/** order by var_pop() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "auth_user_user_permissions" */
export type Auth_User_User_Permissions_Variance_Order_By = {
  id?: Order_By | null | undefined;
  permission_id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "authtoken_token". All fields are combined with a logical 'AND'. */
export type Authtoken_Token_Bool_Exp = {
  _and?: Array<Authtoken_Token_Bool_Exp> | null | undefined;
  _not?: Authtoken_Token_Bool_Exp | null | undefined;
  _or?: Array<Authtoken_Token_Bool_Exp> | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  created?: Timestamptz_Comparison_Exp | null | undefined;
  key?: String_Comparison_Exp | null | undefined;
  user_id?: Int_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "authtoken_token" */
export type Authtoken_Token_Constraint =
  /** unique or primary key constraint on columns "key" */
  | 'authtoken_token_pkey'
  /** unique or primary key constraint on columns "user_id" */
  | 'authtoken_token_user_id_key';

/** input type for inserting data into table "authtoken_token" */
export type Authtoken_Token_Insert_Input = {
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  created?: unknown;
  key?: string | null | undefined;
  user_id?: number | null | undefined;
};

/** input type for inserting object relation for remote table "authtoken_token" */
export type Authtoken_Token_Obj_Rel_Insert_Input = {
  data: Authtoken_Token_Insert_Input;
  /** upsert condition */
  on_conflict?: Authtoken_Token_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "authtoken_token" */
export type Authtoken_Token_On_Conflict = {
  constraint: Authtoken_Token_Constraint;
  update_columns?: Array<Authtoken_Token_Update_Column>;
  where?: Authtoken_Token_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "authtoken_token". */
export type Authtoken_Token_Order_By = {
  auth_user?: Auth_User_Order_By | null | undefined;
  created?: Order_By | null | undefined;
  key?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** update columns of table "authtoken_token" */
export type Authtoken_Token_Update_Column =
  /** column name */
  | 'created'
  /** column name */
  | 'key'
  /** column name */
  | 'user_id';

/** Boolean expression to compare columns of type "bigint". All fields are combined with logical 'AND'. */
export type Bigint_Comparison_Exp = {
  _eq?: unknown;
  _gt?: unknown;
  _gte?: unknown;
  _in?: Array<unknown> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: unknown;
  _lte?: unknown;
  _neq?: unknown;
  _nin?: Array<unknown> | null | undefined;
};

export type Core_Action_Aggregate_Bool_Exp = {
  count?: Core_Action_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Action_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Action_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Action_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_action" */
export type Core_Action_Aggregate_Order_By = {
  avg?: Core_Action_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Action_Max_Order_By | null | undefined;
  min?: Core_Action_Min_Order_By | null | undefined;
  stddev?: Core_Action_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Action_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Action_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Action_Sum_Order_By | null | undefined;
  var_pop?: Core_Action_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Action_Var_Samp_Order_By | null | undefined;
  variance?: Core_Action_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_action" */
export type Core_Action_Arr_Rel_Insert_Input = {
  data: Array<Core_Action_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Action_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_action" */
export type Core_Action_Avg_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_action". All fields are combined with a logical 'AND'. */
export type Core_Action_Bool_Exp = {
  _and?: Array<Core_Action_Bool_Exp> | null | undefined;
  _not?: Core_Action_Bool_Exp | null | undefined;
  _or?: Array<Core_Action_Bool_Exp> | null | undefined;
  agent_role?: String_Comparison_Exp | null | undefined;
  agent_thread_id?: Bigint_Comparison_Exp | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  execution_graph_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  order?: Int_Comparison_Exp | null | undefined;
  plan_id?: Bigint_Comparison_Exp | null | undefined;
  purpose?: Jsonb_Comparison_Exp | null | undefined;
  purpose_text?: String_Comparison_Exp | null | undefined;
  result_summary?: String_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_action" */
export type Core_Action_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_action_pkey';

/** input type for inserting data into table "core_action" */
export type Core_Action_Insert_Input = {
  agent_role?: string | null | undefined;
  agent_thread_id?: unknown;
  completed_at?: unknown;
  created_at?: unknown;
  execution_graph_id?: unknown;
  id?: unknown;
  order?: number | null | undefined;
  plan_id?: unknown;
  purpose?: unknown;
  purpose_text?: string | null | undefined;
  result_summary?: string | null | undefined;
  started_at?: unknown;
  status?: string | null | undefined;
  target_id?: unknown;
};

/** order by max() on columns of table "core_action" */
export type Core_Action_Max_Order_By = {
  agent_role?: Order_By | null | undefined;
  agent_thread_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  purpose_text?: Order_By | null | undefined;
  result_summary?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_action" */
export type Core_Action_Min_Order_By = {
  agent_role?: Order_By | null | undefined;
  agent_thread_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  purpose_text?: Order_By | null | undefined;
  result_summary?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_action" */
export type Core_Action_On_Conflict = {
  constraint: Core_Action_Constraint;
  update_columns?: Array<Core_Action_Update_Column>;
  where?: Core_Action_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_action". */
export type Core_Action_Order_By = {
  agent_role?: Order_By | null | undefined;
  agent_thread_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  purpose?: Order_By | null | undefined;
  purpose_text?: Order_By | null | undefined;
  result_summary?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** select columns of table "core_action" */
export type Core_Action_Select_Column =
  /** column name */
  | 'agent_role'
  /** column name */
  | 'agent_thread_id'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'execution_graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'order'
  /** column name */
  | 'plan_id'
  /** column name */
  | 'purpose'
  /** column name */
  | 'purpose_text'
  /** column name */
  | 'result_summary'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'target_id';

/** input type for updating data in table "core_action" */
export type Core_Action_Set_Input = {
  agent_role?: string | null | undefined;
  agent_thread_id?: unknown;
  completed_at?: unknown;
  created_at?: unknown;
  execution_graph_id?: unknown;
  id?: unknown;
  order?: number | null | undefined;
  plan_id?: unknown;
  purpose?: unknown;
  purpose_text?: string | null | undefined;
  result_summary?: string | null | undefined;
  started_at?: unknown;
  status?: string | null | undefined;
  target_id?: unknown;
};

/** order by stddev() on columns of table "core_action" */
export type Core_Action_Stddev_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_action" */
export type Core_Action_Stddev_Pop_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_action" */
export type Core_Action_Stddev_Samp_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_action" */
export type Core_Action_Sum_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_action" */
export type Core_Action_Update_Column =
  /** column name */
  | 'agent_role'
  /** column name */
  | 'agent_thread_id'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'execution_graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'order'
  /** column name */
  | 'plan_id'
  /** column name */
  | 'purpose'
  /** column name */
  | 'purpose_text'
  /** column name */
  | 'result_summary'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'target_id';

/** order by var_pop() on columns of table "core_action" */
export type Core_Action_Var_Pop_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_action" */
export type Core_Action_Var_Samp_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_action" */
export type Core_Action_Variance_Order_By = {
  agent_thread_id?: Order_By | null | undefined;
  execution_graph_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  order?: Order_By | null | undefined;
  plan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

export type Core_Amassscan_Aggregate_Bool_Exp = {
  count?: Core_Amassscan_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Amassscan_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Amassscan_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Amassscan_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_amassscan" */
export type Core_Amassscan_Aggregate_Order_By = {
  avg?: Core_Amassscan_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Amassscan_Max_Order_By | null | undefined;
  min?: Core_Amassscan_Min_Order_By | null | undefined;
  stddev?: Core_Amassscan_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Amassscan_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Amassscan_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Amassscan_Sum_Order_By | null | undefined;
  var_pop?: Core_Amassscan_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Amassscan_Var_Samp_Order_By | null | undefined;
  variance?: Core_Amassscan_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_amassscan" */
export type Core_Amassscan_Arr_Rel_Insert_Input = {
  data: Array<Core_Amassscan_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Amassscan_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_amassscan" */
export type Core_Amassscan_Avg_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_amassscan". All fields are combined with a logical 'AND'. */
export type Core_Amassscan_Bool_Exp = {
  _and?: Array<Core_Amassscan_Bool_Exp> | null | undefined;
  _not?: Core_Amassscan_Bool_Exp | null | undefined;
  _or?: Array<Core_Amassscan_Bool_Exp> | null | undefined;
  added_count?: Int_Comparison_Exp | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_seed?: Core_Seed_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  which_seed_id?: Bigint_Comparison_Exp | null | undefined;
  which_target_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_amassscan" */
export type Core_Amassscan_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_amassscan_pkey';

/** input type for inserting data into table "core_amassscan" */
export type Core_Amassscan_Insert_Input = {
  added_count?: number | null | undefined;
  completed_at?: unknown;
  core_seed?: Core_Seed_Obj_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  started_at?: unknown;
  status?: string | null | undefined;
  which_seed_id?: unknown;
  which_target_id?: unknown;
};

/** order by max() on columns of table "core_amassscan" */
export type Core_Amassscan_Max_Order_By = {
  added_count?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_amassscan" */
export type Core_Amassscan_Min_Order_By = {
  added_count?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_amassscan" */
export type Core_Amassscan_On_Conflict = {
  constraint: Core_Amassscan_Constraint;
  update_columns?: Array<Core_Amassscan_Update_Column>;
  where?: Core_Amassscan_Bool_Exp | null | undefined;
};

/** select columns of table "core_amassscan" */
export type Core_Amassscan_Select_Column =
  /** column name */
  | 'added_count'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'which_seed_id'
  /** column name */
  | 'which_target_id';

/** order by stddev() on columns of table "core_amassscan" */
export type Core_Amassscan_Stddev_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_amassscan" */
export type Core_Amassscan_Stddev_Pop_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_amassscan" */
export type Core_Amassscan_Stddev_Samp_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_amassscan" */
export type Core_Amassscan_Sum_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** update columns of table "core_amassscan" */
export type Core_Amassscan_Update_Column =
  /** column name */
  | 'added_count'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'which_seed_id'
  /** column name */
  | 'which_target_id';

/** order by var_pop() on columns of table "core_amassscan" */
export type Core_Amassscan_Var_Pop_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_amassscan" */
export type Core_Amassscan_Var_Samp_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_amassscan" */
export type Core_Amassscan_Variance_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
  which_target_id?: Order_By | null | undefined;
};

export type Core_Analysisfinding_Aggregate_Bool_Exp = {
  count?: Core_Analysisfinding_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Analysisfinding_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Analysisfinding_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Analysisfinding_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_analysisfinding" */
export type Core_Analysisfinding_Aggregate_Order_By = {
  avg?: Core_Analysisfinding_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Analysisfinding_Max_Order_By | null | undefined;
  min?: Core_Analysisfinding_Min_Order_By | null | undefined;
  stddev?: Core_Analysisfinding_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Analysisfinding_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Analysisfinding_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Analysisfinding_Sum_Order_By | null | undefined;
  var_pop?: Core_Analysisfinding_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Analysisfinding_Var_Samp_Order_By | null | undefined;
  variance?: Core_Analysisfinding_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_analysisfinding" */
export type Core_Analysisfinding_Arr_Rel_Insert_Input = {
  data: Array<Core_Analysisfinding_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Analysisfinding_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Avg_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_analysisfinding". All fields are combined with a logical 'AND'. */
export type Core_Analysisfinding_Bool_Exp = {
  _and?: Array<Core_Analysisfinding_Bool_Exp> | null | undefined;
  _not?: Core_Analysisfinding_Bool_Exp | null | undefined;
  _or?: Array<Core_Analysisfinding_Bool_Exp> | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  line_number?: Int_Comparison_Exp | null | undefined;
  match_content?: String_Comparison_Exp | null | undefined;
  match_end?: Int_Comparison_Exp | null | undefined;
  match_start?: Int_Comparison_Exp | null | undefined;
  pattern_name?: String_Comparison_Exp | null | undefined;
  which_url_result_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_analysisfinding" */
export type Core_Analysisfinding_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_analysisfinding_pkey'
  /** unique or primary key constraint on columns "line_number", "pattern_name", "which_url_result_id" */
  | 'core_analysisfinding_which_url_result_id_patt_13e0d907_uniq';

/** input type for inserting data into table "core_analysisfinding" */
export type Core_Analysisfinding_Insert_Input = {
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  line_number?: number | null | undefined;
  match_content?: string | null | undefined;
  match_end?: number | null | undefined;
  match_start?: number | null | undefined;
  pattern_name?: string | null | undefined;
  which_url_result_id?: unknown;
};

/** order by max() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_content?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  pattern_name?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_content?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  pattern_name?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_analysisfinding" */
export type Core_Analysisfinding_On_Conflict = {
  constraint: Core_Analysisfinding_Constraint;
  update_columns?: Array<Core_Analysisfinding_Update_Column>;
  where?: Core_Analysisfinding_Bool_Exp | null | undefined;
};

/** select columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Select_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'line_number'
  /** column name */
  | 'match_content'
  /** column name */
  | 'match_end'
  /** column name */
  | 'match_start'
  /** column name */
  | 'pattern_name'
  /** column name */
  | 'which_url_result_id';

/** order by stddev() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Sum_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** update columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'line_number'
  /** column name */
  | 'match_content'
  /** column name */
  | 'match_end'
  /** column name */
  | 'match_start'
  /** column name */
  | 'pattern_name'
  /** column name */
  | 'which_url_result_id';

/** order by var_pop() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_analysisfinding" */
export type Core_Analysisfinding_Variance_Order_By = {
  id?: Order_By | null | undefined;
  line_number?: Order_By | null | undefined;
  match_end?: Order_By | null | undefined;
  match_start?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

export type Core_Analyzedata_Aggregate_Bool_Exp = {
  bool_and?: Core_Analyzedata_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Analyzedata_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Analyzedata_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Analyzedata_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Analyzedata_Select_Column_Core_Analyzedata_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Analyzedata_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Analyzedata_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Analyzedata_Select_Column_Core_Analyzedata_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Analyzedata_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Analyzedata_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Analyzedata_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Analyzedata_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_analyzedata" */
export type Core_Analyzedata_Aggregate_Order_By = {
  avg?: Core_Analyzedata_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Analyzedata_Max_Order_By | null | undefined;
  min?: Core_Analyzedata_Min_Order_By | null | undefined;
  stddev?: Core_Analyzedata_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Analyzedata_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Analyzedata_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Analyzedata_Sum_Order_By | null | undefined;
  var_pop?: Core_Analyzedata_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Analyzedata_Var_Samp_Order_By | null | undefined;
  variance?: Core_Analyzedata_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_analyzedata" */
export type Core_Analyzedata_Arr_Rel_Insert_Input = {
  data: Array<Core_Analyzedata_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Analyzedata_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_analyzedata". All fields are combined with a logical 'AND'. */
export type Core_Analyzedata_Bool_Exp = {
  _and?: Array<Core_Analyzedata_Bool_Exp> | null | undefined;
  _not?: Core_Analyzedata_Bool_Exp | null | undefined;
  _or?: Array<Core_Analyzedata_Bool_Exp> | null | undefined;
  author?: String_Comparison_Exp | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  is_from_ai?: Boolean_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  url_result_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_analyzedata" */
export type Core_Analyzedata_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_analyzedata_pkey';

/** input type for inserting data into table "core_analyzedata" */
export type Core_Analyzedata_Insert_Input = {
  author?: string | null | undefined;
  content?: string | null | undefined;
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  ip_id?: unknown;
  is_from_ai?: boolean | null | undefined;
  subdomain_id?: unknown;
  updated_at?: unknown;
  url_result_id?: unknown;
};

/** order by max() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Max_Order_By = {
  author?: Order_By | null | undefined;
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Min_Order_By = {
  author?: Order_By | null | undefined;
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_analyzedata" */
export type Core_Analyzedata_On_Conflict = {
  constraint: Core_Analyzedata_Constraint;
  update_columns?: Array<Core_Analyzedata_Update_Column>;
  where?: Core_Analyzedata_Bool_Exp | null | undefined;
};

/** select columns of table "core_analyzedata" */
export type Core_Analyzedata_Select_Column =
  /** column name */
  | 'author'
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'is_from_ai'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'url_result_id';

/** select "core_analyzedata_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_analyzedata" */
export type Core_Analyzedata_Select_Column_Core_Analyzedata_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_from_ai';

/** select "core_analyzedata_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_analyzedata" */
export type Core_Analyzedata_Select_Column_Core_Analyzedata_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_from_ai';

/** order by stddev() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** update columns of table "core_analyzedata" */
export type Core_Analyzedata_Update_Column =
  /** column name */
  | 'author'
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'is_from_ai'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'url_result_id';

/** order by var_pop() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_analyzedata" */
export type Core_Analyzedata_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_attackplan". All fields are combined with a logical 'AND'. */
export type Core_Attackplan_Bool_Exp = {
  _and?: Array<Core_Attackplan_Bool_Exp> | null | undefined;
  _not?: Core_Attackplan_Bool_Exp | null | undefined;
  _or?: Array<Core_Attackplan_Bool_Exp> | null | undefined;
  core_actions?: Core_Action_Bool_Exp | null | undefined;
  core_actions_aggregate?: Core_Action_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  objective?: String_Comparison_Exp | null | undefined;
  parent_plan_id?: Bigint_Comparison_Exp | null | undefined;
  scope?: Jsonb_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** input type for inserting data into table "core_attackplan" */
export type Core_Attackplan_Insert_Input = {
  core_actions?: Core_Action_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  objective?: string | null | undefined;
  parent_plan_id?: unknown;
  scope?: unknown;
  status?: string | null | undefined;
  target_id?: unknown;
  thread_id?: unknown;
  updated_at?: unknown;
};

/** Ordering options when selecting data from "core_attackplan". */
export type Core_Attackplan_Order_By = {
  core_actions_aggregate?: Core_Action_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  objective?: Order_By | null | undefined;
  parent_plan_id?: Order_By | null | undefined;
  scope?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** input type for updating data in table "core_attackplan" */
export type Core_Attackplan_Set_Input = {
  created_at?: unknown;
  id?: unknown;
  objective?: string | null | undefined;
  parent_plan_id?: unknown;
  scope?: unknown;
  status?: string | null | undefined;
  target_id?: unknown;
  thread_id?: unknown;
  updated_at?: unknown;
};

export type Core_Attackvector_Aggregate_Bool_Exp = {
  count?: Core_Attackvector_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Attackvector_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Attackvector_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Attackvector_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_attackvector" */
export type Core_Attackvector_Aggregate_Order_By = {
  avg?: Core_Attackvector_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Attackvector_Max_Order_By | null | undefined;
  min?: Core_Attackvector_Min_Order_By | null | undefined;
  stddev?: Core_Attackvector_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Attackvector_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Attackvector_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Attackvector_Sum_Order_By | null | undefined;
  var_pop?: Core_Attackvector_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Attackvector_Var_Samp_Order_By | null | undefined;
  variance?: Core_Attackvector_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_attackvector" */
export type Core_Attackvector_Arr_Rel_Insert_Input = {
  data: Array<Core_Attackvector_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Attackvector_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_attackvector" */
export type Core_Attackvector_Avg_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_attackvector". All fields are combined with a logical 'AND'. */
export type Core_Attackvector_Bool_Exp = {
  _and?: Array<Core_Attackvector_Bool_Exp> | null | undefined;
  _not?: Core_Attackvector_Bool_Exp | null | undefined;
  _or?: Array<Core_Attackvector_Bool_Exp> | null | undefined;
  core_commandtemplates?: Core_Commandtemplate_Bool_Exp | null | undefined;
  core_commandtemplates_aggregate?: Core_Commandtemplate_Aggregate_Bool_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_payloads?: Core_Payload_Bool_Exp | null | undefined;
  core_payloads_aggregate?: Core_Payload_Aggregate_Bool_Exp | null | undefined;
  core_verifications?: Core_Verification_Bool_Exp | null | undefined;
  core_verifications_aggregate?: Core_Verification_Aggregate_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  description?: String_Comparison_Exp | null | undefined;
  evidence?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  risk_score?: Smallint_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  vector_type?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_attackvector" */
export type Core_Attackvector_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_attackvector_pkey';

/** input type for inserting data into table "core_attackvector" */
export type Core_Attackvector_Insert_Input = {
  core_commandtemplates?: Core_Commandtemplate_Arr_Rel_Insert_Input | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_payloads?: Core_Payload_Arr_Rel_Insert_Input | null | undefined;
  core_verifications?: Core_Verification_Arr_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  description?: string | null | undefined;
  evidence?: string | null | undefined;
  id?: unknown;
  name?: string | null | undefined;
  overview_id?: unknown;
  risk_score?: unknown;
  status?: string | null | undefined;
  updated_at?: unknown;
  vector_type?: string | null | undefined;
};

/** order by max() on columns of table "core_attackvector" */
export type Core_Attackvector_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  evidence?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  vector_type?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_attackvector" */
export type Core_Attackvector_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  evidence?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  vector_type?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_attackvector" */
export type Core_Attackvector_Obj_Rel_Insert_Input = {
  data: Core_Attackvector_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Attackvector_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_attackvector" */
export type Core_Attackvector_On_Conflict = {
  constraint: Core_Attackvector_Constraint;
  update_columns?: Array<Core_Attackvector_Update_Column>;
  where?: Core_Attackvector_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_attackvector". */
export type Core_Attackvector_Order_By = {
  core_commandtemplates_aggregate?: Core_Commandtemplate_Aggregate_Order_By | null | undefined;
  core_overview?: Core_Overview_Order_By | null | undefined;
  core_payloads_aggregate?: Core_Payload_Aggregate_Order_By | null | undefined;
  core_verifications_aggregate?: Core_Verification_Aggregate_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  evidence?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  vector_type?: Order_By | null | undefined;
};

/** select columns of table "core_attackvector" */
export type Core_Attackvector_Select_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'description'
  /** column name */
  | 'evidence'
  /** column name */
  | 'id'
  /** column name */
  | 'name'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'risk_score'
  /** column name */
  | 'status'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'vector_type';

/** input type for updating data in table "core_attackvector" */
export type Core_Attackvector_Set_Input = {
  created_at?: unknown;
  description?: string | null | undefined;
  evidence?: string | null | undefined;
  id?: unknown;
  name?: string | null | undefined;
  overview_id?: unknown;
  risk_score?: unknown;
  status?: string | null | undefined;
  updated_at?: unknown;
  vector_type?: string | null | undefined;
};

/** order by stddev() on columns of table "core_attackvector" */
export type Core_Attackvector_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_attackvector" */
export type Core_Attackvector_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_attackvector" */
export type Core_Attackvector_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_attackvector" */
export type Core_Attackvector_Sum_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** update columns of table "core_attackvector" */
export type Core_Attackvector_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'description'
  /** column name */
  | 'evidence'
  /** column name */
  | 'id'
  /** column name */
  | 'name'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'risk_score'
  /** column name */
  | 'status'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'vector_type';

/** order by var_pop() on columns of table "core_attackvector" */
export type Core_Attackvector_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_attackvector" */
export type Core_Attackvector_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_attackvector" */
export type Core_Attackvector_Variance_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
};

export type Core_Commandexecution_Aggregate_Bool_Exp = {
  count?: Core_Commandexecution_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Commandexecution_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Commandexecution_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Commandexecution_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "core_commandexecution" */
export type Core_Commandexecution_Arr_Rel_Insert_Input = {
  data: Array<Core_Commandexecution_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Commandexecution_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "core_commandexecution". All fields are combined with a logical 'AND'. */
export type Core_Commandexecution_Bool_Exp = {
  _and?: Array<Core_Commandexecution_Bool_Exp> | null | undefined;
  _not?: Core_Commandexecution_Bool_Exp | null | undefined;
  _or?: Array<Core_Commandexecution_Bool_Exp> | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_commandtemplate?: Core_Commandtemplate_Bool_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  executed_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  result?: String_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  template_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_commandexecution" */
export type Core_Commandexecution_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_commandexecution_pkey';

/** input type for inserting data into table "core_commandexecution" */
export type Core_Commandexecution_Insert_Input = {
  completed_at?: unknown;
  core_commandtemplate?: Core_Commandtemplate_Obj_Rel_Insert_Input | null | undefined;
  error_message?: string | null | undefined;
  executed_at?: unknown;
  id?: unknown;
  result?: string | null | undefined;
  status?: string | null | undefined;
  template_id?: unknown;
};

/** on_conflict condition type for table "core_commandexecution" */
export type Core_Commandexecution_On_Conflict = {
  constraint: Core_Commandexecution_Constraint;
  update_columns?: Array<Core_Commandexecution_Update_Column>;
  where?: Core_Commandexecution_Bool_Exp | null | undefined;
};

/** select columns of table "core_commandexecution" */
export type Core_Commandexecution_Select_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'executed_at'
  /** column name */
  | 'id'
  /** column name */
  | 'result'
  /** column name */
  | 'status'
  /** column name */
  | 'template_id';

/** update columns of table "core_commandexecution" */
export type Core_Commandexecution_Update_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'executed_at'
  /** column name */
  | 'id'
  /** column name */
  | 'result'
  /** column name */
  | 'status'
  /** column name */
  | 'template_id';

export type Core_Commandtemplate_Aggregate_Bool_Exp = {
  bool_and?: Core_Commandtemplate_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Commandtemplate_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Commandtemplate_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Commandtemplate_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Commandtemplate_Select_Column_Core_Commandtemplate_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Commandtemplate_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Commandtemplate_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Commandtemplate_Select_Column_Core_Commandtemplate_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Commandtemplate_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Commandtemplate_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Commandtemplate_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Commandtemplate_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_commandtemplate" */
export type Core_Commandtemplate_Aggregate_Order_By = {
  avg?: Core_Commandtemplate_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Commandtemplate_Max_Order_By | null | undefined;
  min?: Core_Commandtemplate_Min_Order_By | null | undefined;
  stddev?: Core_Commandtemplate_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Commandtemplate_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Commandtemplate_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Commandtemplate_Sum_Order_By | null | undefined;
  var_pop?: Core_Commandtemplate_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Commandtemplate_Var_Samp_Order_By | null | undefined;
  variance?: Core_Commandtemplate_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_commandtemplate" */
export type Core_Commandtemplate_Arr_Rel_Insert_Input = {
  data: Array<Core_Commandtemplate_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Commandtemplate_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Avg_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_commandtemplate". All fields are combined with a logical 'AND'. */
export type Core_Commandtemplate_Bool_Exp = {
  _and?: Array<Core_Commandtemplate_Bool_Exp> | null | undefined;
  _not?: Core_Commandtemplate_Bool_Exp | null | undefined;
  _or?: Array<Core_Commandtemplate_Bool_Exp> | null | undefined;
  attack_vector_id?: Bigint_Comparison_Exp | null | undefined;
  command?: String_Comparison_Exp | null | undefined;
  core_attackvector?: Core_Attackvector_Bool_Exp | null | undefined;
  core_commandexecutions?: Core_Commandexecution_Bool_Exp | null | undefined;
  core_commandexecutions_aggregate?: Core_Commandexecution_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  description?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  if_system_tool?: Boolean_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  tool_name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_commandtemplate" */
export type Core_Commandtemplate_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_commandtemplate_pkey';

/** input type for inserting data into table "core_commandtemplate" */
export type Core_Commandtemplate_Insert_Input = {
  attack_vector_id?: unknown;
  command?: string | null | undefined;
  core_attackvector?: Core_Attackvector_Obj_Rel_Insert_Input | null | undefined;
  core_commandexecutions?: Core_Commandexecution_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  description?: string | null | undefined;
  id?: unknown;
  if_system_tool?: boolean | null | undefined;
  name?: string | null | undefined;
  tool_name?: string | null | undefined;
};

/** order by max() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Max_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  command?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  tool_name?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Min_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  command?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  tool_name?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_commandtemplate" */
export type Core_Commandtemplate_Obj_Rel_Insert_Input = {
  data: Core_Commandtemplate_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Commandtemplate_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_commandtemplate" */
export type Core_Commandtemplate_On_Conflict = {
  constraint: Core_Commandtemplate_Constraint;
  update_columns?: Array<Core_Commandtemplate_Update_Column>;
  where?: Core_Commandtemplate_Bool_Exp | null | undefined;
};

/** select columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Select_Column =
  /** column name */
  | 'attack_vector_id'
  /** column name */
  | 'command'
  /** column name */
  | 'created_at'
  /** column name */
  | 'description'
  /** column name */
  | 'id'
  /** column name */
  | 'if_system_tool'
  /** column name */
  | 'name'
  /** column name */
  | 'tool_name';

/** select "core_commandtemplate_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Select_Column_Core_Commandtemplate_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'if_system_tool';

/** select "core_commandtemplate_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Select_Column_Core_Commandtemplate_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'if_system_tool';

/** order by stddev() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Stddev_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Stddev_Pop_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Stddev_Samp_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Sum_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** update columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Update_Column =
  /** column name */
  | 'attack_vector_id'
  /** column name */
  | 'command'
  /** column name */
  | 'created_at'
  /** column name */
  | 'description'
  /** column name */
  | 'id'
  /** column name */
  | 'if_system_tool'
  /** column name */
  | 'name'
  /** column name */
  | 'tool_name';

/** order by var_pop() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Var_Pop_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Var_Samp_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_commandtemplate" */
export type Core_Commandtemplate_Variance_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

export type Core_Comment_Aggregate_Bool_Exp = {
  count?: Core_Comment_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Comment_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Comment_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Comment_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_comment" */
export type Core_Comment_Aggregate_Order_By = {
  avg?: Core_Comment_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Comment_Max_Order_By | null | undefined;
  min?: Core_Comment_Min_Order_By | null | undefined;
  stddev?: Core_Comment_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Comment_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Comment_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Comment_Sum_Order_By | null | undefined;
  var_pop?: Core_Comment_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Comment_Var_Samp_Order_By | null | undefined;
  variance?: Core_Comment_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_comment" */
export type Core_Comment_Arr_Rel_Insert_Input = {
  data: Array<Core_Comment_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Comment_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_comment" */
export type Core_Comment_Avg_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_comment". All fields are combined with a logical 'AND'. */
export type Core_Comment_Bool_Exp = {
  _and?: Array<Core_Comment_Bool_Exp> | null | undefined;
  _not?: Core_Comment_Bool_Exp | null | undefined;
  _or?: Array<Core_Comment_Bool_Exp> | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  which_url_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_comment" */
export type Core_Comment_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_comment_pkey';

/** input type for inserting data into table "core_comment" */
export type Core_Comment_Insert_Input = {
  content?: string | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  which_url_id?: unknown;
};

/** order by max() on columns of table "core_comment" */
export type Core_Comment_Max_Order_By = {
  content?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_comment" */
export type Core_Comment_Min_Order_By = {
  content?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_comment" */
export type Core_Comment_On_Conflict = {
  constraint: Core_Comment_Constraint;
  update_columns?: Array<Core_Comment_Update_Column>;
  where?: Core_Comment_Bool_Exp | null | undefined;
};

/** select columns of table "core_comment" */
export type Core_Comment_Select_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'id'
  /** column name */
  | 'which_url_id';

/** order by stddev() on columns of table "core_comment" */
export type Core_Comment_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_comment" */
export type Core_Comment_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_comment" */
export type Core_Comment_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_comment" */
export type Core_Comment_Sum_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** update columns of table "core_comment" */
export type Core_Comment_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'id'
  /** column name */
  | 'which_url_id';

/** order by var_pop() on columns of table "core_comment" */
export type Core_Comment_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_comment" */
export type Core_Comment_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_comment" */
export type Core_Comment_Variance_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_content_blob". All fields are combined with a logical 'AND'. */
export type Core_Content_Blob_Bool_Exp = {
  _and?: Array<Core_Content_Blob_Bool_Exp> | null | undefined;
  _not?: Core_Content_Blob_Bool_Exp | null | undefined;
  _or?: Array<Core_Content_Blob_Bool_Exp> | null | undefined;
  ai_summary?: String_Comparison_Exp | null | undefined;
  content_size?: Int_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  execution_artifacts?: Execution_Artifact_Bool_Exp | null | undefined;
  execution_artifacts_aggregate?: Execution_Artifact_Aggregate_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  page_breakdown?: Jsonb_Comparison_Exp | null | undefined;
  raw_content?: String_Comparison_Exp | null | undefined;
  source_type?: String_Comparison_Exp | null | undefined;
  source_url?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_content_blob" */
export type Core_Content_Blob_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_content_blob_pkey';

/** input type for inserting data into table "core_content_blob" */
export type Core_Content_Blob_Insert_Input = {
  ai_summary?: string | null | undefined;
  content_size?: number | null | undefined;
  created_at?: unknown;
  execution_artifacts?: Execution_Artifact_Arr_Rel_Insert_Input | null | undefined;
  id?: unknown;
  page_breakdown?: unknown;
  raw_content?: string | null | undefined;
  source_type?: string | null | undefined;
  source_url?: string | null | undefined;
};

/** input type for inserting object relation for remote table "core_content_blob" */
export type Core_Content_Blob_Obj_Rel_Insert_Input = {
  data: Core_Content_Blob_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Content_Blob_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_content_blob" */
export type Core_Content_Blob_On_Conflict = {
  constraint: Core_Content_Blob_Constraint;
  update_columns?: Array<Core_Content_Blob_Update_Column>;
  where?: Core_Content_Blob_Bool_Exp | null | undefined;
};

/** update columns of table "core_content_blob" */
export type Core_Content_Blob_Update_Column =
  /** column name */
  | 'ai_summary'
  /** column name */
  | 'content_size'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'page_breakdown'
  /** column name */
  | 'raw_content'
  /** column name */
  | 'source_type'
  /** column name */
  | 'source_url';

/** Boolean expression to filter rows from the table "core_cveintelligence". All fields are combined with a logical 'AND'. */
export type Core_Cveintelligence_Bool_Exp = {
  _and?: Array<Core_Cveintelligence_Bool_Exp> | null | undefined;
  _not?: Core_Cveintelligence_Bool_Exp | null | undefined;
  _or?: Array<Core_Cveintelligence_Bool_Exp> | null | undefined;
  affected_products?: Jsonb_Comparison_Exp | null | undefined;
  cisa_kev?: Boolean_Comparison_Exp | null | undefined;
  core_techstackcvemappings?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  core_techstackcvemappings_aggregate?: Core_Techstackcvemapping_Aggregate_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  cve_id?: String_Comparison_Exp | null | undefined;
  cvss_score?: Float8_Comparison_Exp | null | undefined;
  cvss_vector?: String_Comparison_Exp | null | undefined;
  cwe_ids?: Jsonb_Comparison_Exp | null | undefined;
  data_sources?: Jsonb_Comparison_Exp | null | undefined;
  description?: String_Comparison_Exp | null | undefined;
  epss_score?: Float8_Comparison_Exp | null | undefined;
  exploit_available?: Boolean_Comparison_Exp | null | undefined;
  exploited_in_wild?: Boolean_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  last_checked?: Timestamptz_Comparison_Exp | null | undefined;
  last_modified_date?: Timestamptz_Comparison_Exp | null | undefined;
  published_date?: Timestamptz_Comparison_Exp | null | undefined;
  references?: Jsonb_Comparison_Exp | null | undefined;
  severity?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_cveintelligence" */
export type Core_Cveintelligence_Constraint =
  /** unique or primary key constraint on columns "cve_id" */
  | 'core_cveintelligence_cve_id_key'
  /** unique or primary key constraint on columns "id" */
  | 'core_cveintelligence_pkey';

/** input type for inserting data into table "core_cveintelligence" */
export type Core_Cveintelligence_Insert_Input = {
  affected_products?: unknown;
  cisa_kev?: boolean | null | undefined;
  core_techstackcvemappings?: Core_Techstackcvemapping_Arr_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  cve_id?: string | null | undefined;
  cvss_score?: unknown;
  cvss_vector?: string | null | undefined;
  cwe_ids?: unknown;
  data_sources?: unknown;
  description?: string | null | undefined;
  epss_score?: unknown;
  exploit_available?: boolean | null | undefined;
  exploited_in_wild?: boolean | null | undefined;
  id?: unknown;
  last_checked?: unknown;
  last_modified_date?: unknown;
  published_date?: unknown;
  references?: unknown;
  severity?: string | null | undefined;
  updated_at?: unknown;
};

/** input type for inserting object relation for remote table "core_cveintelligence" */
export type Core_Cveintelligence_Obj_Rel_Insert_Input = {
  data: Core_Cveintelligence_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Cveintelligence_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_cveintelligence" */
export type Core_Cveintelligence_On_Conflict = {
  constraint: Core_Cveintelligence_Constraint;
  update_columns?: Array<Core_Cveintelligence_Update_Column>;
  where?: Core_Cveintelligence_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_cveintelligence". */
export type Core_Cveintelligence_Order_By = {
  affected_products?: Order_By | null | undefined;
  cisa_kev?: Order_By | null | undefined;
  core_techstackcvemappings_aggregate?: Core_Techstackcvemapping_Aggregate_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  cve_id?: Order_By | null | undefined;
  cvss_score?: Order_By | null | undefined;
  cvss_vector?: Order_By | null | undefined;
  cwe_ids?: Order_By | null | undefined;
  data_sources?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  epss_score?: Order_By | null | undefined;
  exploit_available?: Order_By | null | undefined;
  exploited_in_wild?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_checked?: Order_By | null | undefined;
  last_modified_date?: Order_By | null | undefined;
  published_date?: Order_By | null | undefined;
  references?: Order_By | null | undefined;
  severity?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** update columns of table "core_cveintelligence" */
export type Core_Cveintelligence_Update_Column =
  /** column name */
  | 'affected_products'
  /** column name */
  | 'cisa_kev'
  /** column name */
  | 'created_at'
  /** column name */
  | 'cve_id'
  /** column name */
  | 'cvss_score'
  /** column name */
  | 'cvss_vector'
  /** column name */
  | 'cwe_ids'
  /** column name */
  | 'data_sources'
  /** column name */
  | 'description'
  /** column name */
  | 'epss_score'
  /** column name */
  | 'exploit_available'
  /** column name */
  | 'exploited_in_wild'
  /** column name */
  | 'id'
  /** column name */
  | 'last_checked'
  /** column name */
  | 'last_modified_date'
  /** column name */
  | 'published_date'
  /** column name */
  | 'references'
  /** column name */
  | 'severity'
  /** column name */
  | 'updated_at';

export type Core_Dnsrecord_Aggregate_Bool_Exp = {
  count?: Core_Dnsrecord_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Dnsrecord_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Dnsrecord_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Dnsrecord_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_dnsrecord" */
export type Core_Dnsrecord_Aggregate_Order_By = {
  avg?: Core_Dnsrecord_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Dnsrecord_Max_Order_By | null | undefined;
  min?: Core_Dnsrecord_Min_Order_By | null | undefined;
  stddev?: Core_Dnsrecord_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Dnsrecord_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Dnsrecord_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Dnsrecord_Sum_Order_By | null | undefined;
  var_pop?: Core_Dnsrecord_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Dnsrecord_Var_Samp_Order_By | null | undefined;
  variance?: Core_Dnsrecord_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_dnsrecord" */
export type Core_Dnsrecord_Arr_Rel_Insert_Input = {
  data: Array<Core_Dnsrecord_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Dnsrecord_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Avg_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_dnsrecord". All fields are combined with a logical 'AND'. */
export type Core_Dnsrecord_Bool_Exp = {
  _and?: Array<Core_Dnsrecord_Bool_Exp> | null | undefined;
  _not?: Core_Dnsrecord_Bool_Exp | null | undefined;
  _or?: Array<Core_Dnsrecord_Bool_Exp> | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  record_type?: String_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  ttl?: Int_Comparison_Exp | null | undefined;
  value?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_dnsrecord" */
export type Core_Dnsrecord_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_dnsrecord_pkey'
  /** unique or primary key constraint on columns "subdomain_id", "value", "record_type" */
  | 'core_dnsrecord_subdomain_id_record_type_value_5278b6d0_uniq';

/** input type for inserting data into table "core_dnsrecord" */
export type Core_Dnsrecord_Insert_Input = {
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  record_type?: string | null | undefined;
  subdomain_id?: unknown;
  ttl?: number | null | undefined;
  value?: string | null | undefined;
};

/** order by max() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  record_type?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
  value?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  record_type?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
  value?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_dnsrecord" */
export type Core_Dnsrecord_On_Conflict = {
  constraint: Core_Dnsrecord_Constraint;
  update_columns?: Array<Core_Dnsrecord_Update_Column>;
  where?: Core_Dnsrecord_Bool_Exp | null | undefined;
};

/** select columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Select_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'record_type'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'ttl'
  /** column name */
  | 'value';

/** order by stddev() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Sum_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** update columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'record_type'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'ttl'
  /** column name */
  | 'value';

/** order by var_pop() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_dnsrecord" */
export type Core_Dnsrecord_Variance_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  ttl?: Order_By | null | undefined;
};

export type Core_Endpoint_Aggregate_Bool_Exp = {
  count?: Core_Endpoint_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Endpoint_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Endpoint_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Endpoint_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_endpoint" */
export type Core_Endpoint_Aggregate_Order_By = {
  avg?: Core_Endpoint_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Endpoint_Max_Order_By | null | undefined;
  min?: Core_Endpoint_Min_Order_By | null | undefined;
  stddev?: Core_Endpoint_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Endpoint_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Endpoint_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Endpoint_Sum_Order_By | null | undefined;
  var_pop?: Core_Endpoint_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Endpoint_Var_Samp_Order_By | null | undefined;
  variance?: Core_Endpoint_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_endpoint" */
export type Core_Endpoint_Arr_Rel_Insert_Input = {
  data: Array<Core_Endpoint_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Endpoint_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_endpoint" */
export type Core_Endpoint_Avg_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_endpoint". All fields are combined with a logical 'AND'. */
export type Core_Endpoint_Bool_Exp = {
  _and?: Array<Core_Endpoint_Bool_Exp> | null | undefined;
  _not?: Core_Endpoint_Bool_Exp | null | undefined;
  _or?: Array<Core_Endpoint_Bool_Exp> | null | undefined;
  core_endpoint_discovered_by_inline_js?: Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_inline_js_aggregate?: Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_js?: Core_Endpoint_Discovered_By_Js_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_js_aggregate?: Core_Endpoint_Discovered_By_Js_Aggregate_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_scans?: Core_Endpoint_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_scans_aggregate?: Core_Endpoint_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_urls?: Core_Endpoint_Discovered_By_Urls_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_urls_aggregate?: Core_Endpoint_Discovered_By_Urls_Aggregate_Bool_Exp | null | undefined;
  core_endpoint_related_subdomains?: Core_Endpoint_Related_Subdomains_Bool_Exp | null | undefined;
  core_endpoint_related_subdomains_aggregate?: Core_Endpoint_Related_Subdomains_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_urlparameters?: Core_Urlparameter_Bool_Exp | null | undefined;
  core_urlparameters_aggregate?: Core_Urlparameter_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  method?: String_Comparison_Exp | null | undefined;
  path?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_endpoint" */
export type Core_Endpoint_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_endpoint_pkey'
  /** unique or primary key constraint on columns "target_id", "method", "path" */
  | 'core_endpoint_target_id_method_path_3a06270f_uniq';

export type Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Bool_Exp = {
  count?: Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Endpoint_Discovered_By_Inline_Js_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Order_By = {
  avg?: Core_Endpoint_Discovered_By_Inline_Js_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Endpoint_Discovered_By_Inline_Js_Max_Order_By | null | undefined;
  min?: Core_Endpoint_Discovered_By_Inline_Js_Min_Order_By | null | undefined;
  stddev?: Core_Endpoint_Discovered_By_Inline_Js_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Endpoint_Discovered_By_Inline_Js_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Endpoint_Discovered_By_Inline_Js_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Endpoint_Discovered_By_Inline_Js_Sum_Order_By | null | undefined;
  var_pop?: Core_Endpoint_Discovered_By_Inline_Js_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Endpoint_Discovered_By_Inline_Js_Var_Samp_Order_By | null | undefined;
  variance?: Core_Endpoint_Discovered_By_Inline_Js_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Arr_Rel_Insert_Input = {
  data: Array<Core_Endpoint_Discovered_By_Inline_Js_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Endpoint_Discovered_By_Inline_Js_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Avg_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_endpoint_discovered_by_inline_js". All fields are combined with a logical 'AND'. */
export type Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp = {
  _and?: Array<Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp> | null | undefined;
  _not?: Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp | null | undefined;
  _or?: Array<Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp> | null | undefined;
  core_endpoint?: Core_Endpoint_Bool_Exp | null | undefined;
  core_extractedj?: Core_Extractedjs_Bool_Exp | null | undefined;
  endpoint_id?: Bigint_Comparison_Exp | null | undefined;
  extractedjs_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_endpoint_discovered_by_inline_js_pkey'
  /** unique or primary key constraint on columns "endpoint_id", "extractedjs_id" */
  | 'core_endpoint_discovered_endpoint_id_extractedjs__f967d128_uniq';

/** input type for inserting data into table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Insert_Input = {
  core_endpoint?: Core_Endpoint_Obj_Rel_Insert_Input | null | undefined;
  core_extractedj?: Core_Extractedjs_Obj_Rel_Insert_Input | null | undefined;
  endpoint_id?: unknown;
  extractedjs_id?: unknown;
  id?: unknown;
};

/** order by max() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Max_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Min_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_On_Conflict = {
  constraint: Core_Endpoint_Discovered_By_Inline_Js_Constraint;
  update_columns?: Array<Core_Endpoint_Discovered_By_Inline_Js_Update_Column>;
  where?: Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp | null | undefined;
};

/** select columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Select_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'extractedjs_id'
  /** column name */
  | 'id';

/** order by stddev() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Stddev_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Stddev_Pop_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Stddev_Samp_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Sum_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** update columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Update_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'extractedjs_id'
  /** column name */
  | 'id';

/** order by var_pop() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Var_Pop_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Var_Samp_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_endpoint_discovered_by_inline_js" */
export type Core_Endpoint_Discovered_By_Inline_Js_Variance_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  extractedjs_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

export type Core_Endpoint_Discovered_By_Js_Aggregate_Bool_Exp = {
  count?: Core_Endpoint_Discovered_By_Js_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Endpoint_Discovered_By_Js_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Endpoint_Discovered_By_Js_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Endpoint_Discovered_By_Js_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "core_endpoint_discovered_by_js" */
export type Core_Endpoint_Discovered_By_Js_Arr_Rel_Insert_Input = {
  data: Array<Core_Endpoint_Discovered_By_Js_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Endpoint_Discovered_By_Js_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "core_endpoint_discovered_by_js". All fields are combined with a logical 'AND'. */
export type Core_Endpoint_Discovered_By_Js_Bool_Exp = {
  _and?: Array<Core_Endpoint_Discovered_By_Js_Bool_Exp> | null | undefined;
  _not?: Core_Endpoint_Discovered_By_Js_Bool_Exp | null | undefined;
  _or?: Array<Core_Endpoint_Discovered_By_Js_Bool_Exp> | null | undefined;
  core_endpoint?: Core_Endpoint_Bool_Exp | null | undefined;
  core_javascriptfile?: Core_Javascriptfile_Bool_Exp | null | undefined;
  endpoint_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  javascriptfile_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_endpoint_discovered_by_js" */
export type Core_Endpoint_Discovered_By_Js_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_endpoint_discovered_by_js_pkey'
  /** unique or primary key constraint on columns "javascriptfile_id", "endpoint_id" */
  | 'core_endpoint_discovered_endpoint_id_javascriptfi_e3d8ce37_uniq';

/** input type for inserting data into table "core_endpoint_discovered_by_js" */
export type Core_Endpoint_Discovered_By_Js_Insert_Input = {
  core_endpoint?: Core_Endpoint_Obj_Rel_Insert_Input | null | undefined;
  core_javascriptfile?: Core_Javascriptfile_Obj_Rel_Insert_Input | null | undefined;
  endpoint_id?: unknown;
  id?: unknown;
  javascriptfile_id?: unknown;
};

/** on_conflict condition type for table "core_endpoint_discovered_by_js" */
export type Core_Endpoint_Discovered_By_Js_On_Conflict = {
  constraint: Core_Endpoint_Discovered_By_Js_Constraint;
  update_columns?: Array<Core_Endpoint_Discovered_By_Js_Update_Column>;
  where?: Core_Endpoint_Discovered_By_Js_Bool_Exp | null | undefined;
};

/** select columns of table "core_endpoint_discovered_by_js" */
export type Core_Endpoint_Discovered_By_Js_Select_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'javascriptfile_id';

/** update columns of table "core_endpoint_discovered_by_js" */
export type Core_Endpoint_Discovered_By_Js_Update_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'javascriptfile_id';

export type Core_Endpoint_Discovered_By_Scans_Aggregate_Bool_Exp = {
  count?: Core_Endpoint_Discovered_By_Scans_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Endpoint_Discovered_By_Scans_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Endpoint_Discovered_By_Scans_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Endpoint_Discovered_By_Scans_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "core_endpoint_discovered_by_scans" */
export type Core_Endpoint_Discovered_By_Scans_Arr_Rel_Insert_Input = {
  data: Array<Core_Endpoint_Discovered_By_Scans_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Endpoint_Discovered_By_Scans_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "core_endpoint_discovered_by_scans". All fields are combined with a logical 'AND'. */
export type Core_Endpoint_Discovered_By_Scans_Bool_Exp = {
  _and?: Array<Core_Endpoint_Discovered_By_Scans_Bool_Exp> | null | undefined;
  _not?: Core_Endpoint_Discovered_By_Scans_Bool_Exp | null | undefined;
  _or?: Array<Core_Endpoint_Discovered_By_Scans_Bool_Exp> | null | undefined;
  core_endpoint?: Core_Endpoint_Bool_Exp | null | undefined;
  core_urlscan?: Core_Urlscan_Bool_Exp | null | undefined;
  endpoint_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  urlscan_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_endpoint_discovered_by_scans" */
export type Core_Endpoint_Discovered_By_Scans_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_endpoint_discovered_by_scans_pkey'
  /** unique or primary key constraint on columns "endpoint_id", "urlscan_id" */
  | 'core_endpoint_discovered_endpoint_id_urlscan_id_daf53d8d_uniq';

/** input type for inserting data into table "core_endpoint_discovered_by_scans" */
export type Core_Endpoint_Discovered_By_Scans_Insert_Input = {
  core_endpoint?: Core_Endpoint_Obj_Rel_Insert_Input | null | undefined;
  core_urlscan?: Core_Urlscan_Obj_Rel_Insert_Input | null | undefined;
  endpoint_id?: unknown;
  id?: unknown;
  urlscan_id?: unknown;
};

/** on_conflict condition type for table "core_endpoint_discovered_by_scans" */
export type Core_Endpoint_Discovered_By_Scans_On_Conflict = {
  constraint: Core_Endpoint_Discovered_By_Scans_Constraint;
  update_columns?: Array<Core_Endpoint_Discovered_By_Scans_Update_Column>;
  where?: Core_Endpoint_Discovered_By_Scans_Bool_Exp | null | undefined;
};

/** select columns of table "core_endpoint_discovered_by_scans" */
export type Core_Endpoint_Discovered_By_Scans_Select_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'urlscan_id';

/** update columns of table "core_endpoint_discovered_by_scans" */
export type Core_Endpoint_Discovered_By_Scans_Update_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'urlscan_id';

export type Core_Endpoint_Discovered_By_Urls_Aggregate_Bool_Exp = {
  count?: Core_Endpoint_Discovered_By_Urls_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Endpoint_Discovered_By_Urls_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Endpoint_Discovered_By_Urls_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Endpoint_Discovered_By_Urls_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Aggregate_Order_By = {
  avg?: Core_Endpoint_Discovered_By_Urls_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Endpoint_Discovered_By_Urls_Max_Order_By | null | undefined;
  min?: Core_Endpoint_Discovered_By_Urls_Min_Order_By | null | undefined;
  stddev?: Core_Endpoint_Discovered_By_Urls_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Endpoint_Discovered_By_Urls_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Endpoint_Discovered_By_Urls_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Endpoint_Discovered_By_Urls_Sum_Order_By | null | undefined;
  var_pop?: Core_Endpoint_Discovered_By_Urls_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Endpoint_Discovered_By_Urls_Var_Samp_Order_By | null | undefined;
  variance?: Core_Endpoint_Discovered_By_Urls_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Arr_Rel_Insert_Input = {
  data: Array<Core_Endpoint_Discovered_By_Urls_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Endpoint_Discovered_By_Urls_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Avg_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_endpoint_discovered_by_urls". All fields are combined with a logical 'AND'. */
export type Core_Endpoint_Discovered_By_Urls_Bool_Exp = {
  _and?: Array<Core_Endpoint_Discovered_By_Urls_Bool_Exp> | null | undefined;
  _not?: Core_Endpoint_Discovered_By_Urls_Bool_Exp | null | undefined;
  _or?: Array<Core_Endpoint_Discovered_By_Urls_Bool_Exp> | null | undefined;
  core_endpoint?: Core_Endpoint_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  endpoint_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  urlresult_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_endpoint_discovered_by_urls_pkey'
  /** unique or primary key constraint on columns "urlresult_id", "endpoint_id" */
  | 'core_endpoint_discovered_endpoint_id_urlresult_id_8ed1f66d_uniq';

/** input type for inserting data into table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Insert_Input = {
  core_endpoint?: Core_Endpoint_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  endpoint_id?: unknown;
  id?: unknown;
  urlresult_id?: unknown;
};

/** order by max() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Max_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Min_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_On_Conflict = {
  constraint: Core_Endpoint_Discovered_By_Urls_Constraint;
  update_columns?: Array<Core_Endpoint_Discovered_By_Urls_Update_Column>;
  where?: Core_Endpoint_Discovered_By_Urls_Bool_Exp | null | undefined;
};

/** select columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Select_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'urlresult_id';

/** order by stddev() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Stddev_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Stddev_Pop_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Stddev_Samp_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Sum_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** update columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Update_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'urlresult_id';

/** order by var_pop() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Var_Pop_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Var_Samp_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_endpoint_discovered_by_urls" */
export type Core_Endpoint_Discovered_By_Urls_Variance_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** input type for inserting data into table "core_endpoint" */
export type Core_Endpoint_Insert_Input = {
  core_endpoint_discovered_by_inline_js?: Core_Endpoint_Discovered_By_Inline_Js_Arr_Rel_Insert_Input | null | undefined;
  core_endpoint_discovered_by_js?: Core_Endpoint_Discovered_By_Js_Arr_Rel_Insert_Input | null | undefined;
  core_endpoint_discovered_by_scans?: Core_Endpoint_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  core_endpoint_discovered_by_urls?: Core_Endpoint_Discovered_By_Urls_Arr_Rel_Insert_Input | null | undefined;
  core_endpoint_related_subdomains?: Core_Endpoint_Related_Subdomains_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_urlparameters?: Core_Urlparameter_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  last_seen?: unknown;
  method?: string | null | undefined;
  path?: string | null | undefined;
  target_id?: unknown;
};

/** order by max() on columns of table "core_endpoint" */
export type Core_Endpoint_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  path?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_endpoint" */
export type Core_Endpoint_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  path?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_endpoint" */
export type Core_Endpoint_Obj_Rel_Insert_Input = {
  data: Core_Endpoint_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Endpoint_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_endpoint" */
export type Core_Endpoint_On_Conflict = {
  constraint: Core_Endpoint_Constraint;
  update_columns?: Array<Core_Endpoint_Update_Column>;
  where?: Core_Endpoint_Bool_Exp | null | undefined;
};

export type Core_Endpoint_Related_Subdomains_Aggregate_Bool_Exp = {
  count?: Core_Endpoint_Related_Subdomains_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Endpoint_Related_Subdomains_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Endpoint_Related_Subdomains_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Endpoint_Related_Subdomains_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Aggregate_Order_By = {
  avg?: Core_Endpoint_Related_Subdomains_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Endpoint_Related_Subdomains_Max_Order_By | null | undefined;
  min?: Core_Endpoint_Related_Subdomains_Min_Order_By | null | undefined;
  stddev?: Core_Endpoint_Related_Subdomains_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Endpoint_Related_Subdomains_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Endpoint_Related_Subdomains_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Endpoint_Related_Subdomains_Sum_Order_By | null | undefined;
  var_pop?: Core_Endpoint_Related_Subdomains_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Endpoint_Related_Subdomains_Var_Samp_Order_By | null | undefined;
  variance?: Core_Endpoint_Related_Subdomains_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Arr_Rel_Insert_Input = {
  data: Array<Core_Endpoint_Related_Subdomains_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Endpoint_Related_Subdomains_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Avg_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_endpoint_related_subdomains". All fields are combined with a logical 'AND'. */
export type Core_Endpoint_Related_Subdomains_Bool_Exp = {
  _and?: Array<Core_Endpoint_Related_Subdomains_Bool_Exp> | null | undefined;
  _not?: Core_Endpoint_Related_Subdomains_Bool_Exp | null | undefined;
  _or?: Array<Core_Endpoint_Related_Subdomains_Bool_Exp> | null | undefined;
  core_endpoint?: Core_Endpoint_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  endpoint_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Constraint =
  /** unique or primary key constraint on columns "endpoint_id", "subdomain_id" */
  | 'core_endpoint_related_su_endpoint_id_subdomain_id_3c08a877_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_endpoint_related_subdomains_pkey';

/** input type for inserting data into table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Insert_Input = {
  core_endpoint?: Core_Endpoint_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  endpoint_id?: unknown;
  id?: unknown;
  subdomain_id?: unknown;
};

/** order by max() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Max_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Min_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_On_Conflict = {
  constraint: Core_Endpoint_Related_Subdomains_Constraint;
  update_columns?: Array<Core_Endpoint_Related_Subdomains_Update_Column>;
  where?: Core_Endpoint_Related_Subdomains_Bool_Exp | null | undefined;
};

/** select columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Select_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'subdomain_id';

/** order by stddev() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Stddev_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Stddev_Pop_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Stddev_Samp_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Sum_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** update columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Update_Column =
  /** column name */
  | 'endpoint_id'
  /** column name */
  | 'id'
  /** column name */
  | 'subdomain_id';

/** order by var_pop() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Var_Pop_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Var_Samp_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_endpoint_related_subdomains" */
export type Core_Endpoint_Related_Subdomains_Variance_Order_By = {
  endpoint_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** select columns of table "core_endpoint" */
export type Core_Endpoint_Select_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'method'
  /** column name */
  | 'path'
  /** column name */
  | 'target_id';

/** order by stddev() on columns of table "core_endpoint" */
export type Core_Endpoint_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_endpoint" */
export type Core_Endpoint_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_endpoint" */
export type Core_Endpoint_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_endpoint" */
export type Core_Endpoint_Sum_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_endpoint" */
export type Core_Endpoint_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'method'
  /** column name */
  | 'path'
  /** column name */
  | 'target_id';

/** order by var_pop() on columns of table "core_endpoint" */
export type Core_Endpoint_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_endpoint" */
export type Core_Endpoint_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_endpoint" */
export type Core_Endpoint_Variance_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_extractedjs". All fields are combined with a logical 'AND'. */
export type Core_Extractedjs_Bool_Exp = {
  _and?: Array<Core_Extractedjs_Bool_Exp> | null | undefined;
  _not?: Core_Extractedjs_Bool_Exp | null | undefined;
  _or?: Array<Core_Extractedjs_Bool_Exp> | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  content_hash?: String_Comparison_Exp | null | undefined;
  core_endpoint_discovered_by_inline_js?: Core_Endpoint_Discovered_By_Inline_Js_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_inline_js_aggregate?: Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Bool_Exp | null | undefined;
  core_jsonobjects?: Core_Jsonobject_Bool_Exp | null | undefined;
  core_jsonobjects_aggregate?: Core_Jsonobject_Aggregate_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_analyzed?: Boolean_Comparison_Exp | null | undefined;
  which_url_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_extractedjs" */
export type Core_Extractedjs_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_extractedjs_pkey'
  /** unique or primary key constraint on columns "which_url_id" */
  | 'core_extractedjs_which_url_id_key';

/** input type for inserting data into table "core_extractedjs" */
export type Core_Extractedjs_Insert_Input = {
  content?: string | null | undefined;
  content_hash?: string | null | undefined;
  core_endpoint_discovered_by_inline_js?: Core_Endpoint_Discovered_By_Inline_Js_Arr_Rel_Insert_Input | null | undefined;
  core_jsonobjects?: Core_Jsonobject_Arr_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  is_analyzed?: boolean | null | undefined;
  which_url_id?: unknown;
};

/** input type for inserting object relation for remote table "core_extractedjs" */
export type Core_Extractedjs_Obj_Rel_Insert_Input = {
  data: Core_Extractedjs_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Extractedjs_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_extractedjs" */
export type Core_Extractedjs_On_Conflict = {
  constraint: Core_Extractedjs_Constraint;
  update_columns?: Array<Core_Extractedjs_Update_Column>;
  where?: Core_Extractedjs_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_extractedjs". */
export type Core_Extractedjs_Order_By = {
  content?: Order_By | null | undefined;
  content_hash?: Order_By | null | undefined;
  core_endpoint_discovered_by_inline_js_aggregate?: Core_Endpoint_Discovered_By_Inline_Js_Aggregate_Order_By | null | undefined;
  core_jsonobjects_aggregate?: Core_Jsonobject_Aggregate_Order_By | null | undefined;
  core_urlresult?: Core_Urlresult_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  is_analyzed?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** update columns of table "core_extractedjs" */
export type Core_Extractedjs_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'content_hash'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_analyzed'
  /** column name */
  | 'which_url_id';

export type Core_Form_Aggregate_Bool_Exp = {
  count?: Core_Form_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Form_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Form_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Form_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_form" */
export type Core_Form_Aggregate_Order_By = {
  avg?: Core_Form_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Form_Max_Order_By | null | undefined;
  min?: Core_Form_Min_Order_By | null | undefined;
  stddev?: Core_Form_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Form_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Form_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Form_Sum_Order_By | null | undefined;
  var_pop?: Core_Form_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Form_Var_Samp_Order_By | null | undefined;
  variance?: Core_Form_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_form" */
export type Core_Form_Arr_Rel_Insert_Input = {
  data: Array<Core_Form_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Form_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_form" */
export type Core_Form_Avg_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_form". All fields are combined with a logical 'AND'. */
export type Core_Form_Bool_Exp = {
  _and?: Array<Core_Form_Bool_Exp> | null | undefined;
  _not?: Core_Form_Bool_Exp | null | undefined;
  _or?: Array<Core_Form_Bool_Exp> | null | undefined;
  action?: String_Comparison_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  method?: String_Comparison_Exp | null | undefined;
  parameters?: Jsonb_Comparison_Exp | null | undefined;
  which_url_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_form" */
export type Core_Form_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_form_pkey'
  /** unique or primary key constraint on columns "action", "which_url_id", "method" */
  | 'core_form_which_url_id_action_method_9e13495e_uniq';

/** input type for inserting data into table "core_form" */
export type Core_Form_Insert_Input = {
  action?: string | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  method?: string | null | undefined;
  parameters?: unknown;
  which_url_id?: unknown;
};

/** order by max() on columns of table "core_form" */
export type Core_Form_Max_Order_By = {
  action?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_form" */
export type Core_Form_Min_Order_By = {
  action?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_form" */
export type Core_Form_On_Conflict = {
  constraint: Core_Form_Constraint;
  update_columns?: Array<Core_Form_Update_Column>;
  where?: Core_Form_Bool_Exp | null | undefined;
};

/** select columns of table "core_form" */
export type Core_Form_Select_Column =
  /** column name */
  | 'action'
  /** column name */
  | 'id'
  /** column name */
  | 'method'
  /** column name */
  | 'parameters'
  /** column name */
  | 'which_url_id';

/** order by stddev() on columns of table "core_form" */
export type Core_Form_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_form" */
export type Core_Form_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_form" */
export type Core_Form_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_form" */
export type Core_Form_Sum_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** update columns of table "core_form" */
export type Core_Form_Update_Column =
  /** column name */
  | 'action'
  /** column name */
  | 'id'
  /** column name */
  | 'method'
  /** column name */
  | 'parameters'
  /** column name */
  | 'which_url_id';

/** order by var_pop() on columns of table "core_form" */
export type Core_Form_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_form" */
export type Core_Form_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_form" */
export type Core_Form_Variance_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

export type Core_Historicalip_Aggregate_Bool_Exp = {
  count?: Core_Historicalip_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Historicalip_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Historicalip_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalip_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_historicalip" */
export type Core_Historicalip_Aggregate_Order_By = {
  avg?: Core_Historicalip_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Historicalip_Max_Order_By | null | undefined;
  min?: Core_Historicalip_Min_Order_By | null | undefined;
  stddev?: Core_Historicalip_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Historicalip_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Historicalip_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Historicalip_Sum_Order_By | null | undefined;
  var_pop?: Core_Historicalip_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Historicalip_Var_Samp_Order_By | null | undefined;
  variance?: Core_Historicalip_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_historicalip" */
export type Core_Historicalip_Arr_Rel_Insert_Input = {
  data: Array<Core_Historicalip_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Historicalip_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_historicalip" */
export type Core_Historicalip_Avg_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_historicalip". All fields are combined with a logical 'AND'. */
export type Core_Historicalip_Bool_Exp = {
  _and?: Array<Core_Historicalip_Bool_Exp> | null | undefined;
  _not?: Core_Historicalip_Bool_Exp | null | undefined;
  _or?: Array<Core_Historicalip_Bool_Exp> | null | undefined;
  address?: Inet_Comparison_Exp | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  history_change_reason?: String_Comparison_Exp | null | undefined;
  history_date?: Timestamptz_Comparison_Exp | null | undefined;
  history_id?: Int_Comparison_Exp | null | undefined;
  history_type?: String_Comparison_Exp | null | undefined;
  history_user_id?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  version?: Smallint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_historicalip" */
export type Core_Historicalip_Constraint =
  /** unique or primary key constraint on columns "history_id" */
  | 'core_historicalip_pkey';

/** input type for inserting data into table "core_historicalip" */
export type Core_Historicalip_Insert_Input = {
  address?: unknown;
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  history_change_reason?: string | null | undefined;
  history_date?: unknown;
  history_id?: number | null | undefined;
  history_type?: string | null | undefined;
  history_user_id?: number | null | undefined;
  id?: unknown;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  target_id?: unknown;
  version?: unknown;
};

/** order by max() on columns of table "core_historicalip" */
export type Core_Historicalip_Max_Order_By = {
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_historicalip" */
export type Core_Historicalip_Min_Order_By = {
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_historicalip" */
export type Core_Historicalip_On_Conflict = {
  constraint: Core_Historicalip_Constraint;
  update_columns?: Array<Core_Historicalip_Update_Column>;
  where?: Core_Historicalip_Bool_Exp | null | undefined;
};

/** select columns of table "core_historicalip" */
export type Core_Historicalip_Select_Column =
  /** column name */
  | 'address'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'target_id'
  /** column name */
  | 'version';

/** order by stddev() on columns of table "core_historicalip" */
export type Core_Historicalip_Stddev_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_historicalip" */
export type Core_Historicalip_Stddev_Pop_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_historicalip" */
export type Core_Historicalip_Stddev_Samp_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_historicalip" */
export type Core_Historicalip_Sum_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** update columns of table "core_historicalip" */
export type Core_Historicalip_Update_Column =
  /** column name */
  | 'address'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'target_id'
  /** column name */
  | 'version';

/** order by var_pop() on columns of table "core_historicalip" */
export type Core_Historicalip_Var_Pop_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_historicalip" */
export type Core_Historicalip_Var_Samp_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_historicalip" */
export type Core_Historicalip_Variance_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

export type Core_Historicalport_Aggregate_Bool_Exp = {
  count?: Core_Historicalport_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Historicalport_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Historicalport_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalport_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_historicalport" */
export type Core_Historicalport_Aggregate_Order_By = {
  avg?: Core_Historicalport_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Historicalport_Max_Order_By | null | undefined;
  min?: Core_Historicalport_Min_Order_By | null | undefined;
  stddev?: Core_Historicalport_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Historicalport_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Historicalport_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Historicalport_Sum_Order_By | null | undefined;
  var_pop?: Core_Historicalport_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Historicalport_Var_Samp_Order_By | null | undefined;
  variance?: Core_Historicalport_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_historicalport" */
export type Core_Historicalport_Arr_Rel_Insert_Input = {
  data: Array<Core_Historicalport_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Historicalport_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_historicalport" */
export type Core_Historicalport_Avg_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_historicalport". All fields are combined with a logical 'AND'. */
export type Core_Historicalport_Bool_Exp = {
  _and?: Array<Core_Historicalport_Bool_Exp> | null | undefined;
  _not?: Core_Historicalport_Bool_Exp | null | undefined;
  _or?: Array<Core_Historicalport_Bool_Exp> | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  first_seen?: Timestamptz_Comparison_Exp | null | undefined;
  history_change_reason?: String_Comparison_Exp | null | undefined;
  history_date?: Timestamptz_Comparison_Exp | null | undefined;
  history_id?: Int_Comparison_Exp | null | undefined;
  history_type?: String_Comparison_Exp | null | undefined;
  history_user_id?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  port_number?: Int_Comparison_Exp | null | undefined;
  protocol?: String_Comparison_Exp | null | undefined;
  service_name?: String_Comparison_Exp | null | undefined;
  service_version?: String_Comparison_Exp | null | undefined;
  state?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_historicalport" */
export type Core_Historicalport_Constraint =
  /** unique or primary key constraint on columns "history_id" */
  | 'core_historicalport_pkey';

/** input type for inserting data into table "core_historicalport" */
export type Core_Historicalport_Insert_Input = {
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  first_seen?: unknown;
  history_change_reason?: string | null | undefined;
  history_date?: unknown;
  history_id?: number | null | undefined;
  history_type?: string | null | undefined;
  history_user_id?: number | null | undefined;
  id?: unknown;
  ip_id?: unknown;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  last_seen?: unknown;
  port_number?: number | null | undefined;
  protocol?: string | null | undefined;
  service_name?: string | null | undefined;
  service_version?: string | null | undefined;
  state?: string | null | undefined;
};

/** order by max() on columns of table "core_historicalport" */
export type Core_Historicalport_Max_Order_By = {
  first_seen?: Order_By | null | undefined;
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
  protocol?: Order_By | null | undefined;
  service_name?: Order_By | null | undefined;
  service_version?: Order_By | null | undefined;
  state?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_historicalport" */
export type Core_Historicalport_Min_Order_By = {
  first_seen?: Order_By | null | undefined;
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
  protocol?: Order_By | null | undefined;
  service_name?: Order_By | null | undefined;
  service_version?: Order_By | null | undefined;
  state?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_historicalport" */
export type Core_Historicalport_On_Conflict = {
  constraint: Core_Historicalport_Constraint;
  update_columns?: Array<Core_Historicalport_Update_Column>;
  where?: Core_Historicalport_Bool_Exp | null | undefined;
};

/** select columns of table "core_historicalport" */
export type Core_Historicalport_Select_Column =
  /** column name */
  | 'first_seen'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'port_number'
  /** column name */
  | 'protocol'
  /** column name */
  | 'service_name'
  /** column name */
  | 'service_version'
  /** column name */
  | 'state';

/** order by stddev() on columns of table "core_historicalport" */
export type Core_Historicalport_Stddev_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_historicalport" */
export type Core_Historicalport_Stddev_Pop_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_historicalport" */
export type Core_Historicalport_Stddev_Samp_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_historicalport" */
export type Core_Historicalport_Sum_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** update columns of table "core_historicalport" */
export type Core_Historicalport_Update_Column =
  /** column name */
  | 'first_seen'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'port_number'
  /** column name */
  | 'protocol'
  /** column name */
  | 'service_name'
  /** column name */
  | 'service_version'
  /** column name */
  | 'state';

/** order by var_pop() on columns of table "core_historicalport" */
export type Core_Historicalport_Var_Pop_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_historicalport" */
export type Core_Historicalport_Var_Samp_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_historicalport" */
export type Core_Historicalport_Variance_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

export type Core_Historicalsubdomain_Aggregate_Bool_Exp = {
  bool_and?: Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Historicalsubdomain_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Historicalsubdomain_Select_Column_Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalsubdomain_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Historicalsubdomain_Select_Column_Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalsubdomain_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Historicalsubdomain_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Historicalsubdomain_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalsubdomain_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Aggregate_Order_By = {
  avg?: Core_Historicalsubdomain_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Historicalsubdomain_Max_Order_By | null | undefined;
  min?: Core_Historicalsubdomain_Min_Order_By | null | undefined;
  stddev?: Core_Historicalsubdomain_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Historicalsubdomain_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Historicalsubdomain_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Historicalsubdomain_Sum_Order_By | null | undefined;
  var_pop?: Core_Historicalsubdomain_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Historicalsubdomain_Var_Samp_Order_By | null | undefined;
  variance?: Core_Historicalsubdomain_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Arr_Rel_Insert_Input = {
  data: Array<Core_Historicalsubdomain_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Historicalsubdomain_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Avg_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_historicalsubdomain". All fields are combined with a logical 'AND'. */
export type Core_Historicalsubdomain_Bool_Exp = {
  _and?: Array<Core_Historicalsubdomain_Bool_Exp> | null | undefined;
  _not?: Core_Historicalsubdomain_Bool_Exp | null | undefined;
  _or?: Array<Core_Historicalsubdomain_Bool_Exp> | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  cdn_name?: String_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  first_seen?: Timestamptz_Comparison_Exp | null | undefined;
  history_change_reason?: String_Comparison_Exp | null | undefined;
  history_date?: Timestamptz_Comparison_Exp | null | undefined;
  history_id?: Int_Comparison_Exp | null | undefined;
  history_type?: String_Comparison_Exp | null | undefined;
  history_user_id?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_active?: Boolean_Comparison_Exp | null | undefined;
  is_cdn?: Boolean_Comparison_Exp | null | undefined;
  is_resolvable?: Boolean_Comparison_Exp | null | undefined;
  is_tech_analyzed?: Boolean_Comparison_Exp | null | undefined;
  is_waf?: Boolean_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  sources_text?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  waf_name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Constraint =
  /** unique or primary key constraint on columns "history_id" */
  | 'core_historicalsubdomain_pkey';

/** input type for inserting data into table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Insert_Input = {
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  cdn_name?: string | null | undefined;
  created_at?: unknown;
  first_seen?: unknown;
  history_change_reason?: string | null | undefined;
  history_date?: unknown;
  history_id?: number | null | undefined;
  history_type?: string | null | undefined;
  history_user_id?: number | null | undefined;
  id?: unknown;
  is_active?: boolean | null | undefined;
  is_cdn?: boolean | null | undefined;
  is_resolvable?: boolean | null | undefined;
  is_tech_analyzed?: boolean | null | undefined;
  is_waf?: boolean | null | undefined;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  last_seen?: unknown;
  name?: string | null | undefined;
  sources_text?: string | null | undefined;
  target_id?: unknown;
  waf_name?: string | null | undefined;
};

/** order by max() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Max_Order_By = {
  cdn_name?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  first_seen?: Order_By | null | undefined;
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  sources_text?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  waf_name?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Min_Order_By = {
  cdn_name?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  first_seen?: Order_By | null | undefined;
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  sources_text?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  waf_name?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_On_Conflict = {
  constraint: Core_Historicalsubdomain_Constraint;
  update_columns?: Array<Core_Historicalsubdomain_Update_Column>;
  where?: Core_Historicalsubdomain_Bool_Exp | null | undefined;
};

/** select columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Select_Column =
  /** column name */
  | 'cdn_name'
  /** column name */
  | 'created_at'
  /** column name */
  | 'first_seen'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'name'
  /** column name */
  | 'sources_text'
  /** column name */
  | 'target_id'
  /** column name */
  | 'waf_name';

/** select "core_historicalsubdomain_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Select_Column_Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf';

/** select "core_historicalsubdomain_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Select_Column_Core_Historicalsubdomain_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf';

/** order by stddev() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Stddev_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Stddev_Pop_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Stddev_Samp_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Sum_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Update_Column =
  /** column name */
  | 'cdn_name'
  /** column name */
  | 'created_at'
  /** column name */
  | 'first_seen'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'name'
  /** column name */
  | 'sources_text'
  /** column name */
  | 'target_id'
  /** column name */
  | 'waf_name';

/** order by var_pop() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Var_Pop_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Var_Samp_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_historicalsubdomain" */
export type Core_Historicalsubdomain_Variance_Order_By = {
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

export type Core_Historicalurlresult_Aggregate_Bool_Exp = {
  bool_and?: Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Historicalurlresult_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Historicalurlresult_Select_Column_Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalurlresult_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Historicalurlresult_Select_Column_Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalurlresult_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Historicalurlresult_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Historicalurlresult_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Historicalurlresult_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Aggregate_Order_By = {
  avg?: Core_Historicalurlresult_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Historicalurlresult_Max_Order_By | null | undefined;
  min?: Core_Historicalurlresult_Min_Order_By | null | undefined;
  stddev?: Core_Historicalurlresult_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Historicalurlresult_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Historicalurlresult_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Historicalurlresult_Sum_Order_By | null | undefined;
  var_pop?: Core_Historicalurlresult_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Historicalurlresult_Var_Samp_Order_By | null | undefined;
  variance?: Core_Historicalurlresult_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_historicalurlresult" */
export type Core_Historicalurlresult_Arr_Rel_Insert_Input = {
  data: Array<Core_Historicalurlresult_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Historicalurlresult_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Avg_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_historicalurlresult". All fields are combined with a logical 'AND'. */
export type Core_Historicalurlresult_Bool_Exp = {
  _and?: Array<Core_Historicalurlresult_Bool_Exp> | null | undefined;
  _not?: Core_Historicalurlresult_Bool_Exp | null | undefined;
  _or?: Array<Core_Historicalurlresult_Bool_Exp> | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  cleaned_html?: String_Comparison_Exp | null | undefined;
  content_fetch_status?: String_Comparison_Exp | null | undefined;
  content_length?: Int_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  discovery_source?: String_Comparison_Exp | null | undefined;
  dom_snapshot?: String_Comparison_Exp | null | undefined;
  final_url?: String_Comparison_Exp | null | undefined;
  headers?: Jsonb_Comparison_Exp | null | undefined;
  history_change_reason?: String_Comparison_Exp | null | undefined;
  history_date?: Timestamptz_Comparison_Exp | null | undefined;
  history_id?: Int_Comparison_Exp | null | undefined;
  history_type?: String_Comparison_Exp | null | undefined;
  history_user_id?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_external_redirect?: Boolean_Comparison_Exp | null | undefined;
  is_important?: Boolean_Comparison_Exp | null | undefined;
  is_tech_analyzed?: Boolean_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  method?: String_Comparison_Exp | null | undefined;
  raw_response?: String_Comparison_Exp | null | undefined;
  raw_response_hash?: String_Comparison_Exp | null | undefined;
  status_code?: Int_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  text?: String_Comparison_Exp | null | undefined;
  title?: String_Comparison_Exp | null | undefined;
  url?: String_Comparison_Exp | null | undefined;
  used_flaresolverr?: Boolean_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_historicalurlresult" */
export type Core_Historicalurlresult_Constraint =
  /** unique or primary key constraint on columns "history_id" */
  | 'core_historicalurlresult_pkey';

/** input type for inserting data into table "core_historicalurlresult" */
export type Core_Historicalurlresult_Insert_Input = {
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  cleaned_html?: string | null | undefined;
  content_fetch_status?: string | null | undefined;
  content_length?: number | null | undefined;
  created_at?: unknown;
  discovery_source?: string | null | undefined;
  dom_snapshot?: string | null | undefined;
  final_url?: string | null | undefined;
  headers?: unknown;
  history_change_reason?: string | null | undefined;
  history_date?: unknown;
  history_id?: number | null | undefined;
  history_type?: string | null | undefined;
  history_user_id?: number | null | undefined;
  id?: unknown;
  is_external_redirect?: boolean | null | undefined;
  is_important?: boolean | null | undefined;
  is_tech_analyzed?: boolean | null | undefined;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  method?: string | null | undefined;
  raw_response?: string | null | undefined;
  raw_response_hash?: string | null | undefined;
  status_code?: number | null | undefined;
  target_id?: unknown;
  text?: string | null | undefined;
  title?: string | null | undefined;
  url?: string | null | undefined;
  used_flaresolverr?: boolean | null | undefined;
};

/** order by max() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Max_Order_By = {
  cleaned_html?: Order_By | null | undefined;
  content_fetch_status?: Order_By | null | undefined;
  content_length?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  discovery_source?: Order_By | null | undefined;
  dom_snapshot?: Order_By | null | undefined;
  final_url?: Order_By | null | undefined;
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  raw_response?: Order_By | null | undefined;
  raw_response_hash?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  url?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Min_Order_By = {
  cleaned_html?: Order_By | null | undefined;
  content_fetch_status?: Order_By | null | undefined;
  content_length?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  discovery_source?: Order_By | null | undefined;
  dom_snapshot?: Order_By | null | undefined;
  final_url?: Order_By | null | undefined;
  history_change_reason?: Order_By | null | undefined;
  history_date?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_type?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  raw_response?: Order_By | null | undefined;
  raw_response_hash?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  url?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_historicalurlresult" */
export type Core_Historicalurlresult_On_Conflict = {
  constraint: Core_Historicalurlresult_Constraint;
  update_columns?: Array<Core_Historicalurlresult_Update_Column>;
  where?: Core_Historicalurlresult_Bool_Exp | null | undefined;
};

/** select columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Select_Column =
  /** column name */
  | 'cleaned_html'
  /** column name */
  | 'content_fetch_status'
  /** column name */
  | 'content_length'
  /** column name */
  | 'created_at'
  /** column name */
  | 'discovery_source'
  /** column name */
  | 'dom_snapshot'
  /** column name */
  | 'final_url'
  /** column name */
  | 'headers'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'method'
  /** column name */
  | 'raw_response'
  /** column name */
  | 'raw_response_hash'
  /** column name */
  | 'status_code'
  /** column name */
  | 'target_id'
  /** column name */
  | 'text'
  /** column name */
  | 'title'
  /** column name */
  | 'url'
  /** column name */
  | 'used_flaresolverr';

/** select "core_historicalurlresult_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Select_Column_Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'used_flaresolverr';

/** select "core_historicalurlresult_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Select_Column_Core_Historicalurlresult_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'used_flaresolverr';

/** order by stddev() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Stddev_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Stddev_Pop_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Stddev_Samp_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Sum_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Update_Column =
  /** column name */
  | 'cleaned_html'
  /** column name */
  | 'content_fetch_status'
  /** column name */
  | 'content_length'
  /** column name */
  | 'created_at'
  /** column name */
  | 'discovery_source'
  /** column name */
  | 'dom_snapshot'
  /** column name */
  | 'final_url'
  /** column name */
  | 'headers'
  /** column name */
  | 'history_change_reason'
  /** column name */
  | 'history_date'
  /** column name */
  | 'history_id'
  /** column name */
  | 'history_type'
  /** column name */
  | 'history_user_id'
  /** column name */
  | 'id'
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'method'
  /** column name */
  | 'raw_response'
  /** column name */
  | 'raw_response_hash'
  /** column name */
  | 'status_code'
  /** column name */
  | 'target_id'
  /** column name */
  | 'text'
  /** column name */
  | 'title'
  /** column name */
  | 'url'
  /** column name */
  | 'used_flaresolverr';

/** order by var_pop() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Var_Pop_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Var_Samp_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_historicalurlresult" */
export type Core_Historicalurlresult_Variance_Order_By = {
  content_length?: Order_By | null | undefined;
  history_id?: Order_By | null | undefined;
  history_user_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

export type Core_Iframe_Aggregate_Bool_Exp = {
  count?: Core_Iframe_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Iframe_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Iframe_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Iframe_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_iframe" */
export type Core_Iframe_Aggregate_Order_By = {
  avg?: Core_Iframe_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Iframe_Max_Order_By | null | undefined;
  min?: Core_Iframe_Min_Order_By | null | undefined;
  stddev?: Core_Iframe_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Iframe_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Iframe_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Iframe_Sum_Order_By | null | undefined;
  var_pop?: Core_Iframe_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Iframe_Var_Samp_Order_By | null | undefined;
  variance?: Core_Iframe_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_iframe" */
export type Core_Iframe_Arr_Rel_Insert_Input = {
  data: Array<Core_Iframe_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Iframe_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_iframe" */
export type Core_Iframe_Avg_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_iframe". All fields are combined with a logical 'AND'. */
export type Core_Iframe_Bool_Exp = {
  _and?: Array<Core_Iframe_Bool_Exp> | null | undefined;
  _not?: Core_Iframe_Bool_Exp | null | undefined;
  _or?: Array<Core_Iframe_Bool_Exp> | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  src?: String_Comparison_Exp | null | undefined;
  which_url_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_iframe" */
export type Core_Iframe_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_iframe_pkey'
  /** unique or primary key constraint on columns "which_url_id", "src" */
  | 'core_iframe_which_url_id_src_119f620b_uniq';

/** input type for inserting data into table "core_iframe" */
export type Core_Iframe_Insert_Input = {
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  src?: string | null | undefined;
  which_url_id?: unknown;
};

/** order by max() on columns of table "core_iframe" */
export type Core_Iframe_Max_Order_By = {
  id?: Order_By | null | undefined;
  src?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_iframe" */
export type Core_Iframe_Min_Order_By = {
  id?: Order_By | null | undefined;
  src?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_iframe" */
export type Core_Iframe_On_Conflict = {
  constraint: Core_Iframe_Constraint;
  update_columns?: Array<Core_Iframe_Update_Column>;
  where?: Core_Iframe_Bool_Exp | null | undefined;
};

/** select columns of table "core_iframe" */
export type Core_Iframe_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'src'
  /** column name */
  | 'which_url_id';

/** order by stddev() on columns of table "core_iframe" */
export type Core_Iframe_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_iframe" */
export type Core_Iframe_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_iframe" */
export type Core_Iframe_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_iframe" */
export type Core_Iframe_Sum_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** update columns of table "core_iframe" */
export type Core_Iframe_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'src'
  /** column name */
  | 'which_url_id';

/** order by var_pop() on columns of table "core_iframe" */
export type Core_Iframe_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_iframe" */
export type Core_Iframe_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_iframe" */
export type Core_Iframe_Variance_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

export type Core_Initialaianalysis_Aggregate_Bool_Exp = {
  bool_and?: Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Initialaianalysis_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Initialaianalysis_Select_Column_Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Initialaianalysis_Select_Column_Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Initialaianalysis_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Initialaianalysis_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Aggregate_Order_By = {
  avg?: Core_Initialaianalysis_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Initialaianalysis_Max_Order_By | null | undefined;
  min?: Core_Initialaianalysis_Min_Order_By | null | undefined;
  stddev?: Core_Initialaianalysis_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Initialaianalysis_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Initialaianalysis_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Initialaianalysis_Sum_Order_By | null | undefined;
  var_pop?: Core_Initialaianalysis_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Initialaianalysis_Var_Samp_Order_By | null | undefined;
  variance?: Core_Initialaianalysis_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_initialaianalysis" */
export type Core_Initialaianalysis_Arr_Rel_Insert_Input = {
  data: Array<Core_Initialaianalysis_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Initialaianalysis_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_initialaianalysis". All fields are combined with a logical 'AND'. */
export type Core_Initialaianalysis_Bool_Exp = {
  _and?: Array<Core_Initialaianalysis_Bool_Exp> | null | undefined;
  _not?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  _or?: Array<Core_Initialaianalysis_Bool_Exp> | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  inferred_purpose?: String_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  is_converted?: Boolean_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  raw_response?: Jsonb_Comparison_Exp | null | undefined;
  risk_score?: Smallint_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  summary?: String_Comparison_Exp | null | undefined;
  url_result_id?: Bigint_Comparison_Exp | null | undefined;
  worth_deep_analysis?: Boolean_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_initialaianalysis" */
export type Core_Initialaianalysis_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_initialaianalysis_pkey';

/** input type for inserting data into table "core_initialaianalysis" */
export type Core_Initialaianalysis_Insert_Input = {
  completed_at?: unknown;
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  inferred_purpose?: string | null | undefined;
  ip_id?: unknown;
  is_converted?: boolean | null | undefined;
  overview_id?: unknown;
  raw_response?: unknown;
  risk_score?: unknown;
  status?: string | null | undefined;
  subdomain_id?: unknown;
  summary?: string | null | undefined;
  url_result_id?: unknown;
  worth_deep_analysis?: boolean | null | undefined;
};

/** order by max() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Max_Order_By = {
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  inferred_purpose?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Min_Order_By = {
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  inferred_purpose?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_initialaianalysis" */
export type Core_Initialaianalysis_On_Conflict = {
  constraint: Core_Initialaianalysis_Constraint;
  update_columns?: Array<Core_Initialaianalysis_Update_Column>;
  where?: Core_Initialaianalysis_Bool_Exp | null | undefined;
};

/** select columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Select_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'inferred_purpose'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'is_converted'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'raw_response'
  /** column name */
  | 'risk_score'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'summary'
  /** column name */
  | 'url_result_id'
  /** column name */
  | 'worth_deep_analysis';

/** select "core_initialaianalysis_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Select_Column_Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_converted'
  /** column name */
  | 'worth_deep_analysis';

/** select "core_initialaianalysis_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Select_Column_Core_Initialaianalysis_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_converted'
  /** column name */
  | 'worth_deep_analysis';

/** order by stddev() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** update columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Update_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'inferred_purpose'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'is_converted'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'raw_response'
  /** column name */
  | 'risk_score'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'summary'
  /** column name */
  | 'url_result_id'
  /** column name */
  | 'worth_deep_analysis';

/** order by var_pop() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_initialaianalysis" */
export type Core_Initialaianalysis_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  url_result_id?: Order_By | null | undefined;
};

export type Core_Ip_Aggregate_Bool_Exp = {
  count?: Core_Ip_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Ip_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Ip_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Ip_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_ip" */
export type Core_Ip_Aggregate_Order_By = {
  avg?: Core_Ip_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Ip_Max_Order_By | null | undefined;
  min?: Core_Ip_Min_Order_By | null | undefined;
  stddev?: Core_Ip_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Ip_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Ip_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Ip_Sum_Order_By | null | undefined;
  var_pop?: Core_Ip_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Ip_Var_Samp_Order_By | null | undefined;
  variance?: Core_Ip_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_ip" */
export type Core_Ip_Arr_Rel_Insert_Input = {
  data: Array<Core_Ip_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Ip_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_ip" */
export type Core_Ip_Avg_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_ip". All fields are combined with a logical 'AND'. */
export type Core_Ip_Bool_Exp = {
  _and?: Array<Core_Ip_Bool_Exp> | null | undefined;
  _not?: Core_Ip_Bool_Exp | null | undefined;
  _or?: Array<Core_Ip_Bool_Exp> | null | undefined;
  address?: Inet_Comparison_Exp | null | undefined;
  core_analyzedata?: Core_Analyzedata_Bool_Exp | null | undefined;
  core_analyzedata_aggregate?: Core_Analyzedata_Aggregate_Bool_Exp | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Bool_Exp | null | undefined;
  core_ip_discovered_by_scans?: Core_Ip_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_ip_discovered_by_scans_aggregate?: Core_Ip_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  core_ip_which_seeds?: Core_Ip_Which_Seed_Bool_Exp | null | undefined;
  core_ip_which_seeds_aggregate?: Core_Ip_Which_Seed_Aggregate_Bool_Exp | null | undefined;
  core_nucleiscans?: Core_Nucleiscan_Bool_Exp | null | undefined;
  core_nucleiscans_aggregate?: Core_Nucleiscan_Aggregate_Bool_Exp | null | undefined;
  core_overview_ips?: Core_Overview_Ips_Bool_Exp | null | undefined;
  core_overview_ips_aggregate?: Core_Overview_Ips_Aggregate_Bool_Exp | null | undefined;
  core_ports?: Core_Port_Bool_Exp | null | undefined;
  core_ports_aggregate?: Core_Port_Aggregate_Bool_Exp | null | undefined;
  core_subdomain_ips?: Core_Subdomain_Ips_Bool_Exp | null | undefined;
  core_subdomain_ips_aggregate?: Core_Subdomain_Ips_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  version?: Smallint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_ip" */
export type Core_Ip_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_ip_pkey';

export type Core_Ip_Discovered_By_Scans_Aggregate_Bool_Exp = {
  count?: Core_Ip_Discovered_By_Scans_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Ip_Discovered_By_Scans_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Ip_Discovered_By_Scans_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Ip_Discovered_By_Scans_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Aggregate_Order_By = {
  avg?: Core_Ip_Discovered_By_Scans_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Ip_Discovered_By_Scans_Max_Order_By | null | undefined;
  min?: Core_Ip_Discovered_By_Scans_Min_Order_By | null | undefined;
  stddev?: Core_Ip_Discovered_By_Scans_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Ip_Discovered_By_Scans_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Ip_Discovered_By_Scans_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Ip_Discovered_By_Scans_Sum_Order_By | null | undefined;
  var_pop?: Core_Ip_Discovered_By_Scans_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Ip_Discovered_By_Scans_Var_Samp_Order_By | null | undefined;
  variance?: Core_Ip_Discovered_By_Scans_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Arr_Rel_Insert_Input = {
  data: Array<Core_Ip_Discovered_By_Scans_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Ip_Discovered_By_Scans_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_ip_discovered_by_scans". All fields are combined with a logical 'AND'. */
export type Core_Ip_Discovered_By_Scans_Bool_Exp = {
  _and?: Array<Core_Ip_Discovered_By_Scans_Bool_Exp> | null | undefined;
  _not?: Core_Ip_Discovered_By_Scans_Bool_Exp | null | undefined;
  _or?: Array<Core_Ip_Discovered_By_Scans_Bool_Exp> | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_nmapscan?: Core_Nmapscan_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  nmapscan_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Constraint =
  /** unique or primary key constraint on columns "nmapscan_id", "ip_id" */
  | 'core_ip_discovered_by_scans_ip_id_nmapscan_id_562e8262_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_ip_discovered_by_scans_pkey';

/** input type for inserting data into table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Insert_Input = {
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_nmapscan?: Core_Nmapscan_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  ip_id?: unknown;
  nmapscan_id?: unknown;
};

/** order by max() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Max_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Min_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_On_Conflict = {
  constraint: Core_Ip_Discovered_By_Scans_Constraint;
  update_columns?: Array<Core_Ip_Discovered_By_Scans_Update_Column>;
  where?: Core_Ip_Discovered_By_Scans_Bool_Exp | null | undefined;
};

/** select columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'nmapscan_id';

/** order by stddev() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** update columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'nmapscan_id';

/** order by var_pop() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_ip_discovered_by_scans" */
export type Core_Ip_Discovered_By_Scans_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
};

/** input type for inserting data into table "core_ip" */
export type Core_Ip_Insert_Input = {
  address?: unknown;
  core_analyzedata?: Core_Analyzedata_Arr_Rel_Insert_Input | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Arr_Rel_Insert_Input | null | undefined;
  core_ip_discovered_by_scans?: Core_Ip_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  core_ip_which_seeds?: Core_Ip_Which_Seed_Arr_Rel_Insert_Input | null | undefined;
  core_nucleiscans?: Core_Nucleiscan_Arr_Rel_Insert_Input | null | undefined;
  core_overview_ips?: Core_Overview_Ips_Arr_Rel_Insert_Input | null | undefined;
  core_ports?: Core_Port_Arr_Rel_Insert_Input | null | undefined;
  core_subdomain_ips?: Core_Subdomain_Ips_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  id?: unknown;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  target_id?: unknown;
  version?: unknown;
};

/** order by max() on columns of table "core_ip" */
export type Core_Ip_Max_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_ip" */
export type Core_Ip_Min_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_ip" */
export type Core_Ip_Obj_Rel_Insert_Input = {
  data: Core_Ip_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Ip_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_ip" */
export type Core_Ip_On_Conflict = {
  constraint: Core_Ip_Constraint;
  update_columns?: Array<Core_Ip_Update_Column>;
  where?: Core_Ip_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_ip". */
export type Core_Ip_Order_By = {
  address?: Order_By | null | undefined;
  core_analyzedata_aggregate?: Core_Analyzedata_Aggregate_Order_By | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Order_By | null | undefined;
  core_ip_discovered_by_scans_aggregate?: Core_Ip_Discovered_By_Scans_Aggregate_Order_By | null | undefined;
  core_ip_which_seeds_aggregate?: Core_Ip_Which_Seed_Aggregate_Order_By | null | undefined;
  core_nucleiscans_aggregate?: Core_Nucleiscan_Aggregate_Order_By | null | undefined;
  core_overview_ips_aggregate?: Core_Overview_Ips_Aggregate_Order_By | null | undefined;
  core_ports_aggregate?: Core_Port_Aggregate_Order_By | null | undefined;
  core_subdomain_ips_aggregate?: Core_Subdomain_Ips_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** select columns of table "core_ip" */
export type Core_Ip_Select_Column =
  /** column name */
  | 'address'
  /** column name */
  | 'id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'target_id'
  /** column name */
  | 'version';

/** order by stddev() on columns of table "core_ip" */
export type Core_Ip_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_ip" */
export type Core_Ip_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_ip" */
export type Core_Ip_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_ip" */
export type Core_Ip_Sum_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** update columns of table "core_ip" */
export type Core_Ip_Update_Column =
  /** column name */
  | 'address'
  /** column name */
  | 'id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'target_id'
  /** column name */
  | 'version';

/** order by var_pop() on columns of table "core_ip" */
export type Core_Ip_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_ip" */
export type Core_Ip_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_ip" */
export type Core_Ip_Variance_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
};

export type Core_Ip_Which_Seed_Aggregate_Bool_Exp = {
  count?: Core_Ip_Which_Seed_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Ip_Which_Seed_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Ip_Which_Seed_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Ip_Which_Seed_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Aggregate_Order_By = {
  avg?: Core_Ip_Which_Seed_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Ip_Which_Seed_Max_Order_By | null | undefined;
  min?: Core_Ip_Which_Seed_Min_Order_By | null | undefined;
  stddev?: Core_Ip_Which_Seed_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Ip_Which_Seed_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Ip_Which_Seed_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Ip_Which_Seed_Sum_Order_By | null | undefined;
  var_pop?: Core_Ip_Which_Seed_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Ip_Which_Seed_Var_Samp_Order_By | null | undefined;
  variance?: Core_Ip_Which_Seed_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Arr_Rel_Insert_Input = {
  data: Array<Core_Ip_Which_Seed_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Ip_Which_Seed_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_ip_which_seed". All fields are combined with a logical 'AND'. */
export type Core_Ip_Which_Seed_Bool_Exp = {
  _and?: Array<Core_Ip_Which_Seed_Bool_Exp> | null | undefined;
  _not?: Core_Ip_Which_Seed_Bool_Exp | null | undefined;
  _or?: Array<Core_Ip_Which_Seed_Bool_Exp> | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_seed?: Core_Seed_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  seed_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Constraint =
  /** unique or primary key constraint on columns "seed_id", "ip_id" */
  | 'core_ip_which_seed_ip_id_seed_id_530bbc53_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_ip_which_seed_pkey';

/** input type for inserting data into table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Insert_Input = {
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_seed?: Core_Seed_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  ip_id?: unknown;
  seed_id?: unknown;
};

/** order by max() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Max_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Min_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_On_Conflict = {
  constraint: Core_Ip_Which_Seed_Constraint;
  update_columns?: Array<Core_Ip_Which_Seed_Update_Column>;
  where?: Core_Ip_Which_Seed_Bool_Exp | null | undefined;
};

/** select columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'seed_id';

/** order by stddev() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** update columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'seed_id';

/** order by var_pop() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_ip_which_seed" */
export type Core_Ip_Which_Seed_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_javascriptfile". All fields are combined with a logical 'AND'. */
export type Core_Javascriptfile_Bool_Exp = {
  _and?: Array<Core_Javascriptfile_Bool_Exp> | null | undefined;
  _not?: Core_Javascriptfile_Bool_Exp | null | undefined;
  _or?: Array<Core_Javascriptfile_Bool_Exp> | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  content_hash?: String_Comparison_Exp | null | undefined;
  core_endpoint_discovered_by_js?: Core_Endpoint_Discovered_By_Js_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_js_aggregate?: Core_Endpoint_Discovered_By_Js_Aggregate_Bool_Exp | null | undefined;
  core_javascriptfile_related_pages?: Core_Javascriptfile_Related_Pages_Bool_Exp | null | undefined;
  core_javascriptfile_related_pages_aggregate?: Core_Javascriptfile_Related_Pages_Aggregate_Bool_Exp | null | undefined;
  core_jsonobjects?: Core_Jsonobject_Bool_Exp | null | undefined;
  core_jsonobjects_aggregate?: Core_Jsonobject_Aggregate_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_analyzed?: Boolean_Comparison_Exp | null | undefined;
  is_source_map?: Boolean_Comparison_Exp | null | undefined;
  last_error?: String_Comparison_Exp | null | undefined;
  retry_count?: Int_Comparison_Exp | null | undefined;
  source_map_sources?: Jsonb_Comparison_Exp | null | undefined;
  src?: String_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_javascriptfile" */
export type Core_Javascriptfile_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_javascriptfile_pkey';

/** input type for inserting data into table "core_javascriptfile" */
export type Core_Javascriptfile_Insert_Input = {
  content?: string | null | undefined;
  content_hash?: string | null | undefined;
  core_endpoint_discovered_by_js?: Core_Endpoint_Discovered_By_Js_Arr_Rel_Insert_Input | null | undefined;
  core_javascriptfile_related_pages?: Core_Javascriptfile_Related_Pages_Arr_Rel_Insert_Input | null | undefined;
  core_jsonobjects?: Core_Jsonobject_Arr_Rel_Insert_Input | null | undefined;
  id?: unknown;
  is_analyzed?: boolean | null | undefined;
  is_source_map?: boolean | null | undefined;
  last_error?: string | null | undefined;
  retry_count?: number | null | undefined;
  source_map_sources?: unknown;
  src?: string | null | undefined;
  status?: string | null | undefined;
};

/** input type for inserting object relation for remote table "core_javascriptfile" */
export type Core_Javascriptfile_Obj_Rel_Insert_Input = {
  data: Core_Javascriptfile_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Javascriptfile_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_javascriptfile" */
export type Core_Javascriptfile_On_Conflict = {
  constraint: Core_Javascriptfile_Constraint;
  update_columns?: Array<Core_Javascriptfile_Update_Column>;
  where?: Core_Javascriptfile_Bool_Exp | null | undefined;
};

export type Core_Javascriptfile_Related_Pages_Aggregate_Bool_Exp = {
  count?: Core_Javascriptfile_Related_Pages_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Javascriptfile_Related_Pages_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Javascriptfile_Related_Pages_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Javascriptfile_Related_Pages_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Aggregate_Order_By = {
  avg?: Core_Javascriptfile_Related_Pages_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Javascriptfile_Related_Pages_Max_Order_By | null | undefined;
  min?: Core_Javascriptfile_Related_Pages_Min_Order_By | null | undefined;
  stddev?: Core_Javascriptfile_Related_Pages_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Javascriptfile_Related_Pages_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Javascriptfile_Related_Pages_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Javascriptfile_Related_Pages_Sum_Order_By | null | undefined;
  var_pop?: Core_Javascriptfile_Related_Pages_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Javascriptfile_Related_Pages_Var_Samp_Order_By | null | undefined;
  variance?: Core_Javascriptfile_Related_Pages_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Arr_Rel_Insert_Input = {
  data: Array<Core_Javascriptfile_Related_Pages_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Javascriptfile_Related_Pages_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Avg_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_javascriptfile_related_pages". All fields are combined with a logical 'AND'. */
export type Core_Javascriptfile_Related_Pages_Bool_Exp = {
  _and?: Array<Core_Javascriptfile_Related_Pages_Bool_Exp> | null | undefined;
  _not?: Core_Javascriptfile_Related_Pages_Bool_Exp | null | undefined;
  _or?: Array<Core_Javascriptfile_Related_Pages_Bool_Exp> | null | undefined;
  core_javascriptfile?: Core_Javascriptfile_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  javascriptfile_id?: Bigint_Comparison_Exp | null | undefined;
  urlresult_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Constraint =
  /** unique or primary key constraint on columns "urlresult_id", "javascriptfile_id" */
  | 'core_javascriptfile_rela_javascriptfile_id_urlres_e4269142_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_javascriptfile_related_pages_pkey';

/** input type for inserting data into table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Insert_Input = {
  core_javascriptfile?: Core_Javascriptfile_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  javascriptfile_id?: unknown;
  urlresult_id?: unknown;
};

/** order by max() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Max_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Min_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_On_Conflict = {
  constraint: Core_Javascriptfile_Related_Pages_Constraint;
  update_columns?: Array<Core_Javascriptfile_Related_Pages_Update_Column>;
  where?: Core_Javascriptfile_Related_Pages_Bool_Exp | null | undefined;
};

/** select columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'javascriptfile_id'
  /** column name */
  | 'urlresult_id';

/** order by stddev() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Sum_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** update columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'javascriptfile_id'
  /** column name */
  | 'urlresult_id';

/** order by var_pop() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_javascriptfile_related_pages" */
export type Core_Javascriptfile_Related_Pages_Variance_Order_By = {
  id?: Order_By | null | undefined;
  javascriptfile_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** update columns of table "core_javascriptfile" */
export type Core_Javascriptfile_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'content_hash'
  /** column name */
  | 'id'
  /** column name */
  | 'is_analyzed'
  /** column name */
  | 'is_source_map'
  /** column name */
  | 'last_error'
  /** column name */
  | 'retry_count'
  /** column name */
  | 'source_map_sources'
  /** column name */
  | 'src'
  /** column name */
  | 'status';

export type Core_Jsonobject_Aggregate_Bool_Exp = {
  avg?: Core_Jsonobject_Aggregate_Bool_Exp_Avg | null | undefined;
  corr?: Core_Jsonobject_Aggregate_Bool_Exp_Corr | null | undefined;
  count?: Core_Jsonobject_Aggregate_Bool_Exp_Count | null | undefined;
  covar_samp?: Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp | null | undefined;
  max?: Core_Jsonobject_Aggregate_Bool_Exp_Max | null | undefined;
  min?: Core_Jsonobject_Aggregate_Bool_Exp_Min | null | undefined;
  stddev_samp?: Core_Jsonobject_Aggregate_Bool_Exp_Stddev_Samp | null | undefined;
  sum?: Core_Jsonobject_Aggregate_Bool_Exp_Sum | null | undefined;
  var_samp?: Core_Jsonobject_Aggregate_Bool_Exp_Var_Samp | null | undefined;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Avg = {
  arguments: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Avg_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Corr = {
  arguments: Core_Jsonobject_Aggregate_Bool_Exp_Corr_Arguments;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Corr_Arguments = {
  X: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Corr_Arguments_Columns;
  Y: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Corr_Arguments_Columns;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Jsonobject_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp = {
  arguments: Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp_Arguments;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp_Arguments = {
  X: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns;
  Y: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Max = {
  arguments: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Max_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Min = {
  arguments: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Min_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Stddev_Samp = {
  arguments: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Stddev_Samp_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Sum = {
  arguments: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Sum_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Jsonobject_Aggregate_Bool_Exp_Var_Samp = {
  arguments: Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Var_Samp_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Jsonobject_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

/** order by aggregate values of table "core_jsonobject" */
export type Core_Jsonobject_Aggregate_Order_By = {
  avg?: Core_Jsonobject_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Jsonobject_Max_Order_By | null | undefined;
  min?: Core_Jsonobject_Min_Order_By | null | undefined;
  stddev?: Core_Jsonobject_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Jsonobject_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Jsonobject_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Jsonobject_Sum_Order_By | null | undefined;
  var_pop?: Core_Jsonobject_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Jsonobject_Var_Samp_Order_By | null | undefined;
  variance?: Core_Jsonobject_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_jsonobject" */
export type Core_Jsonobject_Arr_Rel_Insert_Input = {
  data: Array<Core_Jsonobject_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Jsonobject_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Avg_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_jsonobject". All fields are combined with a logical 'AND'. */
export type Core_Jsonobject_Bool_Exp = {
  _and?: Array<Core_Jsonobject_Bool_Exp> | null | undefined;
  _not?: Core_Jsonobject_Bool_Exp | null | undefined;
  _or?: Array<Core_Jsonobject_Bool_Exp> | null | undefined;
  core_extractedj?: Core_Extractedjs_Bool_Exp | null | undefined;
  core_javascriptfile?: Core_Javascriptfile_Bool_Exp | null | undefined;
  depth?: Int_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  key?: String_Comparison_Exp | null | undefined;
  path?: String_Comparison_Exp | null | undefined;
  score?: Float8_Comparison_Exp | null | undefined;
  struct?: String_Comparison_Exp | null | undefined;
  val?: String_Comparison_Exp | null | undefined;
  which_extracted_js_id?: Bigint_Comparison_Exp | null | undefined;
  which_javascript_file_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_jsonobject" */
export type Core_Jsonobject_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_jsonobject_pkey';

/** input type for inserting data into table "core_jsonobject" */
export type Core_Jsonobject_Insert_Input = {
  core_extractedj?: Core_Extractedjs_Obj_Rel_Insert_Input | null | undefined;
  core_javascriptfile?: Core_Javascriptfile_Obj_Rel_Insert_Input | null | undefined;
  depth?: number | null | undefined;
  id?: unknown;
  key?: string | null | undefined;
  path?: string | null | undefined;
  score?: unknown;
  struct?: string | null | undefined;
  val?: string | null | undefined;
  which_extracted_js_id?: unknown;
  which_javascript_file_id?: unknown;
};

/** order by max() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Max_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  key?: Order_By | null | undefined;
  path?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  struct?: Order_By | null | undefined;
  val?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Min_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  key?: Order_By | null | undefined;
  path?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  struct?: Order_By | null | undefined;
  val?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_jsonobject" */
export type Core_Jsonobject_On_Conflict = {
  constraint: Core_Jsonobject_Constraint;
  update_columns?: Array<Core_Jsonobject_Update_Column>;
  where?: Core_Jsonobject_Bool_Exp | null | undefined;
};

/** select columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column =
  /** column name */
  | 'depth'
  /** column name */
  | 'id'
  /** column name */
  | 'key'
  /** column name */
  | 'path'
  /** column name */
  | 'score'
  /** column name */
  | 'struct'
  /** column name */
  | 'val'
  /** column name */
  | 'which_extracted_js_id'
  /** column name */
  | 'which_javascript_file_id';

/** select "core_jsonobject_aggregate_bool_exp_avg_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Avg_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_corr_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Corr_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_covar_samp_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_max_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Max_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_min_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Min_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_stddev_samp_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Stddev_Samp_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_sum_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Sum_Arguments_Columns =
  /** column name */
  | 'score';

/** select "core_jsonobject_aggregate_bool_exp_var_samp_arguments_columns" columns of table "core_jsonobject" */
export type Core_Jsonobject_Select_Column_Core_Jsonobject_Aggregate_Bool_Exp_Var_Samp_Arguments_Columns =
  /** column name */
  | 'score';

/** order by stddev() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Stddev_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Stddev_Pop_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Stddev_Samp_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Sum_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** update columns of table "core_jsonobject" */
export type Core_Jsonobject_Update_Column =
  /** column name */
  | 'depth'
  /** column name */
  | 'id'
  /** column name */
  | 'key'
  /** column name */
  | 'path'
  /** column name */
  | 'score'
  /** column name */
  | 'struct'
  /** column name */
  | 'val'
  /** column name */
  | 'which_extracted_js_id'
  /** column name */
  | 'which_javascript_file_id';

/** order by var_pop() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Var_Pop_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Var_Samp_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_jsonobject" */
export type Core_Jsonobject_Variance_Order_By = {
  depth?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  score?: Order_By | null | undefined;
  which_extracted_js_id?: Order_By | null | undefined;
  which_javascript_file_id?: Order_By | null | undefined;
};

export type Core_Link_Aggregate_Bool_Exp = {
  count?: Core_Link_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Link_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Link_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Link_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_link" */
export type Core_Link_Aggregate_Order_By = {
  avg?: Core_Link_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Link_Max_Order_By | null | undefined;
  min?: Core_Link_Min_Order_By | null | undefined;
  stddev?: Core_Link_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Link_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Link_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Link_Sum_Order_By | null | undefined;
  var_pop?: Core_Link_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Link_Var_Samp_Order_By | null | undefined;
  variance?: Core_Link_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_link" */
export type Core_Link_Arr_Rel_Insert_Input = {
  data: Array<Core_Link_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Link_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_link" */
export type Core_Link_Avg_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_link". All fields are combined with a logical 'AND'. */
export type Core_Link_Bool_Exp = {
  _and?: Array<Core_Link_Bool_Exp> | null | undefined;
  _not?: Core_Link_Bool_Exp | null | undefined;
  _or?: Array<Core_Link_Bool_Exp> | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  href?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  text?: String_Comparison_Exp | null | undefined;
  which_url_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_link" */
export type Core_Link_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_link_pkey';

/** input type for inserting data into table "core_link" */
export type Core_Link_Insert_Input = {
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  href?: string | null | undefined;
  id?: unknown;
  text?: string | null | undefined;
  which_url_id?: unknown;
};

/** order by max() on columns of table "core_link" */
export type Core_Link_Max_Order_By = {
  href?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_link" */
export type Core_Link_Min_Order_By = {
  href?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_link" */
export type Core_Link_On_Conflict = {
  constraint: Core_Link_Constraint;
  update_columns?: Array<Core_Link_Update_Column>;
  where?: Core_Link_Bool_Exp | null | undefined;
};

/** select columns of table "core_link" */
export type Core_Link_Select_Column =
  /** column name */
  | 'href'
  /** column name */
  | 'id'
  /** column name */
  | 'text'
  /** column name */
  | 'which_url_id';

/** order by stddev() on columns of table "core_link" */
export type Core_Link_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_link" */
export type Core_Link_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_link" */
export type Core_Link_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_link" */
export type Core_Link_Sum_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** update columns of table "core_link" */
export type Core_Link_Update_Column =
  /** column name */
  | 'href'
  /** column name */
  | 'id'
  /** column name */
  | 'text'
  /** column name */
  | 'which_url_id';

/** order by var_pop() on columns of table "core_link" */
export type Core_Link_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_link" */
export type Core_Link_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_link" */
export type Core_Link_Variance_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

export type Core_Metatag_Aggregate_Bool_Exp = {
  count?: Core_Metatag_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Metatag_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Metatag_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Metatag_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_metatag" */
export type Core_Metatag_Aggregate_Order_By = {
  avg?: Core_Metatag_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Metatag_Max_Order_By | null | undefined;
  min?: Core_Metatag_Min_Order_By | null | undefined;
  stddev?: Core_Metatag_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Metatag_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Metatag_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Metatag_Sum_Order_By | null | undefined;
  var_pop?: Core_Metatag_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Metatag_Var_Samp_Order_By | null | undefined;
  variance?: Core_Metatag_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_metatag" */
export type Core_Metatag_Arr_Rel_Insert_Input = {
  data: Array<Core_Metatag_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Metatag_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_metatag" */
export type Core_Metatag_Avg_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_metatag". All fields are combined with a logical 'AND'. */
export type Core_Metatag_Bool_Exp = {
  _and?: Array<Core_Metatag_Bool_Exp> | null | undefined;
  _not?: Core_Metatag_Bool_Exp | null | undefined;
  _or?: Array<Core_Metatag_Bool_Exp> | null | undefined;
  attributes?: Jsonb_Comparison_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  which_url_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_metatag" */
export type Core_Metatag_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_metatag_pkey';

/** input type for inserting data into table "core_metatag" */
export type Core_Metatag_Insert_Input = {
  attributes?: unknown;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  which_url_id?: unknown;
};

/** order by max() on columns of table "core_metatag" */
export type Core_Metatag_Max_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_metatag" */
export type Core_Metatag_Min_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_metatag" */
export type Core_Metatag_On_Conflict = {
  constraint: Core_Metatag_Constraint;
  update_columns?: Array<Core_Metatag_Update_Column>;
  where?: Core_Metatag_Bool_Exp | null | undefined;
};

/** select columns of table "core_metatag" */
export type Core_Metatag_Select_Column =
  /** column name */
  | 'attributes'
  /** column name */
  | 'id'
  /** column name */
  | 'which_url_id';

/** order by stddev() on columns of table "core_metatag" */
export type Core_Metatag_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_metatag" */
export type Core_Metatag_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_metatag" */
export type Core_Metatag_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_metatag" */
export type Core_Metatag_Sum_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** update columns of table "core_metatag" */
export type Core_Metatag_Update_Column =
  /** column name */
  | 'attributes'
  /** column name */
  | 'id'
  /** column name */
  | 'which_url_id';

/** order by var_pop() on columns of table "core_metatag" */
export type Core_Metatag_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_metatag" */
export type Core_Metatag_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_metatag" */
export type Core_Metatag_Variance_Order_By = {
  id?: Order_By | null | undefined;
  which_url_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_nmapscan". All fields are combined with a logical 'AND'. */
export type Core_Nmapscan_Bool_Exp = {
  _and?: Array<Core_Nmapscan_Bool_Exp> | null | undefined;
  _not?: Core_Nmapscan_Bool_Exp | null | undefined;
  _or?: Array<Core_Nmapscan_Bool_Exp> | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_ip_discovered_by_scans?: Core_Ip_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_ip_discovered_by_scans_aggregate?: Core_Ip_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  core_nmapscan_which_seeds?: Core_Nmapscan_Which_Seed_Bool_Exp | null | undefined;
  core_nmapscan_which_seeds_aggregate?: Core_Nmapscan_Which_Seed_Aggregate_Bool_Exp | null | undefined;
  core_port_discovered_by_scans?: Core_Port_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_port_discovered_by_scans_aggregate?: Core_Port_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  nmap_args?: String_Comparison_Exp | null | undefined;
  nmap_output?: String_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_nmapscan" */
export type Core_Nmapscan_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_nmapscan_pkey';

/** input type for inserting data into table "core_nmapscan" */
export type Core_Nmapscan_Insert_Input = {
  completed_at?: unknown;
  core_ip_discovered_by_scans?: Core_Ip_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  core_nmapscan_which_seeds?: Core_Nmapscan_Which_Seed_Arr_Rel_Insert_Input | null | undefined;
  core_port_discovered_by_scans?: Core_Port_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  nmap_args?: string | null | undefined;
  nmap_output?: string | null | undefined;
  started_at?: unknown;
  status?: string | null | undefined;
};

/** input type for inserting object relation for remote table "core_nmapscan" */
export type Core_Nmapscan_Obj_Rel_Insert_Input = {
  data: Core_Nmapscan_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Nmapscan_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_nmapscan" */
export type Core_Nmapscan_On_Conflict = {
  constraint: Core_Nmapscan_Constraint;
  update_columns?: Array<Core_Nmapscan_Update_Column>;
  where?: Core_Nmapscan_Bool_Exp | null | undefined;
};

/** update columns of table "core_nmapscan" */
export type Core_Nmapscan_Update_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'nmap_args'
  /** column name */
  | 'nmap_output'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status';

export type Core_Nmapscan_Which_Seed_Aggregate_Bool_Exp = {
  count?: Core_Nmapscan_Which_Seed_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Nmapscan_Which_Seed_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Nmapscan_Which_Seed_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Nmapscan_Which_Seed_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Aggregate_Order_By = {
  avg?: Core_Nmapscan_Which_Seed_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Nmapscan_Which_Seed_Max_Order_By | null | undefined;
  min?: Core_Nmapscan_Which_Seed_Min_Order_By | null | undefined;
  stddev?: Core_Nmapscan_Which_Seed_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Nmapscan_Which_Seed_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Nmapscan_Which_Seed_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Nmapscan_Which_Seed_Sum_Order_By | null | undefined;
  var_pop?: Core_Nmapscan_Which_Seed_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Nmapscan_Which_Seed_Var_Samp_Order_By | null | undefined;
  variance?: Core_Nmapscan_Which_Seed_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Arr_Rel_Insert_Input = {
  data: Array<Core_Nmapscan_Which_Seed_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Nmapscan_Which_Seed_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Avg_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_nmapscan_which_seed". All fields are combined with a logical 'AND'. */
export type Core_Nmapscan_Which_Seed_Bool_Exp = {
  _and?: Array<Core_Nmapscan_Which_Seed_Bool_Exp> | null | undefined;
  _not?: Core_Nmapscan_Which_Seed_Bool_Exp | null | undefined;
  _or?: Array<Core_Nmapscan_Which_Seed_Bool_Exp> | null | undefined;
  core_nmapscan?: Core_Nmapscan_Bool_Exp | null | undefined;
  core_seed?: Core_Seed_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  nmapscan_id?: Bigint_Comparison_Exp | null | undefined;
  seed_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Constraint =
  /** unique or primary key constraint on columns "nmapscan_id", "seed_id" */
  | 'core_nmapscan_which_seed_nmapscan_id_seed_id_ce5ecc88_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_nmapscan_which_seed_pkey';

/** input type for inserting data into table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Insert_Input = {
  core_nmapscan?: Core_Nmapscan_Obj_Rel_Insert_Input | null | undefined;
  core_seed?: Core_Seed_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  nmapscan_id?: unknown;
  seed_id?: unknown;
};

/** order by max() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Max_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Min_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_On_Conflict = {
  constraint: Core_Nmapscan_Which_Seed_Constraint;
  update_columns?: Array<Core_Nmapscan_Which_Seed_Update_Column>;
  where?: Core_Nmapscan_Which_Seed_Bool_Exp | null | undefined;
};

/** select columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'nmapscan_id'
  /** column name */
  | 'seed_id';

/** order by stddev() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Sum_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** update columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'nmapscan_id'
  /** column name */
  | 'seed_id';

/** order by var_pop() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_nmapscan_which_seed" */
export type Core_Nmapscan_Which_Seed_Variance_Order_By = {
  id?: Order_By | null | undefined;
  nmapscan_id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
};

export type Core_Nucleiscan_Aggregate_Bool_Exp = {
  count?: Core_Nucleiscan_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Nucleiscan_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Nucleiscan_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Nucleiscan_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_nucleiscan" */
export type Core_Nucleiscan_Aggregate_Order_By = {
  avg?: Core_Nucleiscan_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Nucleiscan_Max_Order_By | null | undefined;
  min?: Core_Nucleiscan_Min_Order_By | null | undefined;
  stddev?: Core_Nucleiscan_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Nucleiscan_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Nucleiscan_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Nucleiscan_Sum_Order_By | null | undefined;
  var_pop?: Core_Nucleiscan_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Nucleiscan_Var_Samp_Order_By | null | undefined;
  variance?: Core_Nucleiscan_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_nucleiscan" */
export type Core_Nucleiscan_Arr_Rel_Insert_Input = {
  data: Array<Core_Nucleiscan_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Nucleiscan_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_nucleiscan". All fields are combined with a logical 'AND'. */
export type Core_Nucleiscan_Bool_Exp = {
  _and?: Array<Core_Nucleiscan_Bool_Exp> | null | undefined;
  _not?: Core_Nucleiscan_Bool_Exp | null | undefined;
  _or?: Array<Core_Nucleiscan_Bool_Exp> | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_asset_id?: Bigint_Comparison_Exp | null | undefined;
  output_file?: String_Comparison_Exp | null | undefined;
  severity_filter?: String_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  subdomain_asset_id?: Bigint_Comparison_Exp | null | undefined;
  template_ids?: Jsonb_Comparison_Exp | null | undefined;
  url_asset_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_nucleiscan" */
export type Core_Nucleiscan_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_nucleiscan_pkey';

/** input type for inserting data into table "core_nucleiscan" */
export type Core_Nucleiscan_Insert_Input = {
  completed_at?: unknown;
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  ip_asset_id?: unknown;
  output_file?: string | null | undefined;
  severity_filter?: string | null | undefined;
  started_at?: unknown;
  status?: string | null | undefined;
  subdomain_asset_id?: unknown;
  template_ids?: unknown;
  url_asset_id?: unknown;
};

/** order by max() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Max_Order_By = {
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  output_file?: Order_By | null | undefined;
  severity_filter?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Min_Order_By = {
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  output_file?: Order_By | null | undefined;
  severity_filter?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_nucleiscan" */
export type Core_Nucleiscan_On_Conflict = {
  constraint: Core_Nucleiscan_Constraint;
  update_columns?: Array<Core_Nucleiscan_Update_Column>;
  where?: Core_Nucleiscan_Bool_Exp | null | undefined;
};

/** select columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Select_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_asset_id'
  /** column name */
  | 'output_file'
  /** column name */
  | 'severity_filter'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_asset_id'
  /** column name */
  | 'template_ids'
  /** column name */
  | 'url_asset_id';

/** order by stddev() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** update columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Update_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_asset_id'
  /** column name */
  | 'output_file'
  /** column name */
  | 'severity_filter'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_asset_id'
  /** column name */
  | 'template_ids'
  /** column name */
  | 'url_asset_id';

/** order by var_pop() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_nucleiscan" */
export type Core_Nucleiscan_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

export type Core_Overview_Aggregate_Bool_Exp = {
  count?: Core_Overview_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Overview_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Overview_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Overview_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_overview" */
export type Core_Overview_Aggregate_Order_By = {
  avg?: Core_Overview_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Overview_Max_Order_By | null | undefined;
  min?: Core_Overview_Min_Order_By | null | undefined;
  stddev?: Core_Overview_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Overview_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Overview_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Overview_Sum_Order_By | null | undefined;
  var_pop?: Core_Overview_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Overview_Var_Samp_Order_By | null | undefined;
  variance?: Core_Overview_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_overview" */
export type Core_Overview_Arr_Rel_Insert_Input = {
  data: Array<Core_Overview_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Overview_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_overview" */
export type Core_Overview_Avg_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_overview". All fields are combined with a logical 'AND'. */
export type Core_Overview_Bool_Exp = {
  _and?: Array<Core_Overview_Bool_Exp> | null | undefined;
  _not?: Core_Overview_Bool_Exp | null | undefined;
  _or?: Array<Core_Overview_Bool_Exp> | null | undefined;
  aiAssistantThreadByThreadId?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_threads?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_threads_aggregate?: Ai_Assistant_Thread_Aggregate_Bool_Exp | null | undefined;
  business_impact?: String_Comparison_Exp | null | undefined;
  core_attackvectors?: Core_Attackvector_Bool_Exp | null | undefined;
  core_attackvectors_aggregate?: Core_Attackvector_Aggregate_Bool_Exp | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Bool_Exp | null | undefined;
  core_overview_ips?: Core_Overview_Ips_Bool_Exp | null | undefined;
  core_overview_ips_aggregate?: Core_Overview_Ips_Aggregate_Bool_Exp | null | undefined;
  core_overview_pages?: Core_Overview_Page_Bool_Exp | null | undefined;
  core_overview_pages_aggregate?: Core_Overview_Page_Aggregate_Bool_Exp | null | undefined;
  core_overview_subdomains?: Core_Overview_Subdomains_Bool_Exp | null | undefined;
  core_overview_subdomains_aggregate?: Core_Overview_Subdomains_Aggregate_Bool_Exp | null | undefined;
  core_overview_url_results?: Core_Overview_Url_Results_Bool_Exp | null | undefined;
  core_overview_url_results_aggregate?: Core_Overview_Url_Results_Aggregate_Bool_Exp | null | undefined;
  core_seed?: Core_Seed_Bool_Exp | null | undefined;
  core_subagent_dispatches?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  core_subagent_dispatches_aggregate?: Core_Subagent_Dispatch_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  knowledge?: Jsonb_Comparison_Exp | null | undefined;
  mission_reviews?: Mission_Review_Bool_Exp | null | undefined;
  mission_reviews_aggregate?: Mission_Review_Aggregate_Bool_Exp | null | undefined;
  parent_thread_id?: Bigint_Comparison_Exp | null | undefined;
  port_service?: Jsonb_Comparison_Exp | null | undefined;
  recon_summary?: String_Comparison_Exp | null | undefined;
  rescue_count?: Smallint_Comparison_Exp | null | undefined;
  risk_score?: Smallint_Comparison_Exp | null | undefined;
  seed_id?: Bigint_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  subdomain_intel?: Jsonb_Comparison_Exp | null | undefined;
  summary?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  tech_stack?: Jsonb_Comparison_Exp | null | undefined;
  techs?: Jsonb_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  vuln_intel?: Jsonb_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_overview" */
export type Core_Overview_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_overview_pkey'
  /** unique or primary key constraint on columns "target_id" */
  | 'core_overview_target_id_1ebe185e_uniq';

/** input type for inserting data into table "core_overview" */
export type Core_Overview_Insert_Input = {
  aiAssistantThreadByThreadId?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  ai_assistant_threads?: Ai_Assistant_Thread_Arr_Rel_Insert_Input | null | undefined;
  business_impact?: string | null | undefined;
  core_attackvectors?: Core_Attackvector_Arr_Rel_Insert_Input | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Arr_Rel_Insert_Input | null | undefined;
  core_overview_ips?: Core_Overview_Ips_Arr_Rel_Insert_Input | null | undefined;
  core_overview_pages?: Core_Overview_Page_Arr_Rel_Insert_Input | null | undefined;
  core_overview_subdomains?: Core_Overview_Subdomains_Arr_Rel_Insert_Input | null | undefined;
  core_overview_url_results?: Core_Overview_Url_Results_Arr_Rel_Insert_Input | null | undefined;
  core_seed?: Core_Seed_Obj_Rel_Insert_Input | null | undefined;
  core_subagent_dispatches?: Core_Subagent_Dispatch_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  knowledge?: unknown;
  mission_reviews?: Mission_Review_Arr_Rel_Insert_Input | null | undefined;
  parent_thread_id?: unknown;
  port_service?: unknown;
  recon_summary?: string | null | undefined;
  rescue_count?: unknown;
  risk_score?: unknown;
  seed_id?: unknown;
  status?: string | null | undefined;
  subdomain_intel?: unknown;
  summary?: string | null | undefined;
  target_id?: unknown;
  tech_stack?: unknown;
  techs?: unknown;
  thread_id?: unknown;
  updated_at?: unknown;
  vuln_intel?: unknown;
};

export type Core_Overview_Ips_Aggregate_Bool_Exp = {
  count?: Core_Overview_Ips_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Overview_Ips_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Overview_Ips_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Overview_Ips_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_overview_ips" */
export type Core_Overview_Ips_Aggregate_Order_By = {
  avg?: Core_Overview_Ips_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Overview_Ips_Max_Order_By | null | undefined;
  min?: Core_Overview_Ips_Min_Order_By | null | undefined;
  stddev?: Core_Overview_Ips_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Overview_Ips_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Overview_Ips_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Overview_Ips_Sum_Order_By | null | undefined;
  var_pop?: Core_Overview_Ips_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Overview_Ips_Var_Samp_Order_By | null | undefined;
  variance?: Core_Overview_Ips_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_overview_ips" */
export type Core_Overview_Ips_Arr_Rel_Insert_Input = {
  data: Array<Core_Overview_Ips_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Overview_Ips_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_overview_ips". All fields are combined with a logical 'AND'. */
export type Core_Overview_Ips_Bool_Exp = {
  _and?: Array<Core_Overview_Ips_Bool_Exp> | null | undefined;
  _not?: Core_Overview_Ips_Bool_Exp | null | undefined;
  _or?: Array<Core_Overview_Ips_Bool_Exp> | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_overview_ips" */
export type Core_Overview_Ips_Constraint =
  /** unique or primary key constraint on columns "overview_id", "ip_id" */
  | 'core_overview_ips_overview_id_ip_id_f96f8060_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_overview_ips_pkey';

/** input type for inserting data into table "core_overview_ips" */
export type Core_Overview_Ips_Insert_Input = {
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  ip_id?: unknown;
  overview_id?: unknown;
};

/** order by max() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Max_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Min_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_overview_ips" */
export type Core_Overview_Ips_On_Conflict = {
  constraint: Core_Overview_Ips_Constraint;
  update_columns?: Array<Core_Overview_Ips_Update_Column>;
  where?: Core_Overview_Ips_Bool_Exp | null | undefined;
};

/** select columns of table "core_overview_ips" */
export type Core_Overview_Ips_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'overview_id';

/** order by stddev() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** update columns of table "core_overview_ips" */
export type Core_Overview_Ips_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'overview_id';

/** order by var_pop() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_overview_ips" */
export type Core_Overview_Ips_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by max() on columns of table "core_overview" */
export type Core_Overview_Max_Order_By = {
  business_impact?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  recon_summary?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_overview" */
export type Core_Overview_Min_Order_By = {
  business_impact?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  recon_summary?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_overview" */
export type Core_Overview_Obj_Rel_Insert_Input = {
  data: Core_Overview_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Overview_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_overview" */
export type Core_Overview_On_Conflict = {
  constraint: Core_Overview_Constraint;
  update_columns?: Array<Core_Overview_Update_Column>;
  where?: Core_Overview_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_overview". */
export type Core_Overview_Order_By = {
  aiAssistantThreadByThreadId?: Ai_Assistant_Thread_Order_By | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Order_By | null | undefined;
  ai_assistant_threads_aggregate?: Ai_Assistant_Thread_Aggregate_Order_By | null | undefined;
  business_impact?: Order_By | null | undefined;
  core_attackvectors_aggregate?: Core_Attackvector_Aggregate_Order_By | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Order_By | null | undefined;
  core_overview_ips_aggregate?: Core_Overview_Ips_Aggregate_Order_By | null | undefined;
  core_overview_pages_aggregate?: Core_Overview_Page_Aggregate_Order_By | null | undefined;
  core_overview_subdomains_aggregate?: Core_Overview_Subdomains_Aggregate_Order_By | null | undefined;
  core_overview_url_results_aggregate?: Core_Overview_Url_Results_Aggregate_Order_By | null | undefined;
  core_seed?: Core_Seed_Order_By | null | undefined;
  core_subagent_dispatches_aggregate?: Core_Subagent_Dispatch_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  knowledge?: Order_By | null | undefined;
  mission_reviews_aggregate?: Mission_Review_Aggregate_Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  port_service?: Order_By | null | undefined;
  recon_summary?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_intel?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  tech_stack?: Order_By | null | undefined;
  techs?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  vuln_intel?: Order_By | null | undefined;
};

export type Core_Overview_Page_Aggregate_Bool_Exp = {
  count?: Core_Overview_Page_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Overview_Page_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Overview_Page_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Overview_Page_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_overview_page" */
export type Core_Overview_Page_Aggregate_Order_By = {
  avg?: Core_Overview_Page_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Overview_Page_Max_Order_By | null | undefined;
  min?: Core_Overview_Page_Min_Order_By | null | undefined;
  stddev?: Core_Overview_Page_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Overview_Page_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Overview_Page_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Overview_Page_Sum_Order_By | null | undefined;
  var_pop?: Core_Overview_Page_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Overview_Page_Var_Samp_Order_By | null | undefined;
  variance?: Core_Overview_Page_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_overview_page" */
export type Core_Overview_Page_Arr_Rel_Insert_Input = {
  data: Array<Core_Overview_Page_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Overview_Page_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_overview_page" */
export type Core_Overview_Page_Avg_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_overview_page". All fields are combined with a logical 'AND'. */
export type Core_Overview_Page_Bool_Exp = {
  _and?: Array<Core_Overview_Page_Bool_Exp> | null | undefined;
  _not?: Core_Overview_Page_Bool_Exp | null | undefined;
  _or?: Array<Core_Overview_Page_Bool_Exp> | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  page_breakdown?: Jsonb_Comparison_Exp | null | undefined;
  section_type?: String_Comparison_Exp | null | undefined;
  source_agent?: String_Comparison_Exp | null | undefined;
  summary?: String_Comparison_Exp | null | undefined;
  title?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_overview_page" */
export type Core_Overview_Page_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_overview_page_pkey';

/** input type for inserting data into table "core_overview_page" */
export type Core_Overview_Page_Insert_Input = {
  content?: string | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  overview_id?: unknown;
  page_breakdown?: unknown;
  section_type?: string | null | undefined;
  source_agent?: string | null | undefined;
  summary?: string | null | undefined;
  title?: string | null | undefined;
  updated_at?: unknown;
};

/** order by max() on columns of table "core_overview_page" */
export type Core_Overview_Page_Max_Order_By = {
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  section_type?: Order_By | null | undefined;
  source_agent?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_overview_page" */
export type Core_Overview_Page_Min_Order_By = {
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  section_type?: Order_By | null | undefined;
  source_agent?: Order_By | null | undefined;
  summary?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_overview_page" */
export type Core_Overview_Page_On_Conflict = {
  constraint: Core_Overview_Page_Constraint;
  update_columns?: Array<Core_Overview_Page_Update_Column>;
  where?: Core_Overview_Page_Bool_Exp | null | undefined;
};

/** select columns of table "core_overview_page" */
export type Core_Overview_Page_Select_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'page_breakdown'
  /** column name */
  | 'section_type'
  /** column name */
  | 'source_agent'
  /** column name */
  | 'summary'
  /** column name */
  | 'title'
  /** column name */
  | 'updated_at';

/** order by stddev() on columns of table "core_overview_page" */
export type Core_Overview_Page_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_overview_page" */
export type Core_Overview_Page_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_overview_page" */
export type Core_Overview_Page_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_overview_page" */
export type Core_Overview_Page_Sum_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** update columns of table "core_overview_page" */
export type Core_Overview_Page_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'page_breakdown'
  /** column name */
  | 'section_type'
  /** column name */
  | 'source_agent'
  /** column name */
  | 'summary'
  /** column name */
  | 'title'
  /** column name */
  | 'updated_at';

/** order by var_pop() on columns of table "core_overview_page" */
export type Core_Overview_Page_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_overview_page" */
export type Core_Overview_Page_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_overview_page" */
export type Core_Overview_Page_Variance_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
};

/** select columns of table "core_overview" */
export type Core_Overview_Select_Column =
  /** column name */
  | 'business_impact'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'knowledge'
  /** column name */
  | 'parent_thread_id'
  /** column name */
  | 'port_service'
  /** column name */
  | 'recon_summary'
  /** column name */
  | 'rescue_count'
  /** column name */
  | 'risk_score'
  /** column name */
  | 'seed_id'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_intel'
  /** column name */
  | 'summary'
  /** column name */
  | 'target_id'
  /** column name */
  | 'tech_stack'
  /** column name */
  | 'techs'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'vuln_intel';

/** order by stddev() on columns of table "core_overview" */
export type Core_Overview_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_overview" */
export type Core_Overview_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_overview" */
export type Core_Overview_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

export type Core_Overview_Subdomains_Aggregate_Bool_Exp = {
  count?: Core_Overview_Subdomains_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Overview_Subdomains_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Overview_Subdomains_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Overview_Subdomains_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Aggregate_Order_By = {
  avg?: Core_Overview_Subdomains_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Overview_Subdomains_Max_Order_By | null | undefined;
  min?: Core_Overview_Subdomains_Min_Order_By | null | undefined;
  stddev?: Core_Overview_Subdomains_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Overview_Subdomains_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Overview_Subdomains_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Overview_Subdomains_Sum_Order_By | null | undefined;
  var_pop?: Core_Overview_Subdomains_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Overview_Subdomains_Var_Samp_Order_By | null | undefined;
  variance?: Core_Overview_Subdomains_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Arr_Rel_Insert_Input = {
  data: Array<Core_Overview_Subdomains_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Overview_Subdomains_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Avg_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_overview_subdomains". All fields are combined with a logical 'AND'. */
export type Core_Overview_Subdomains_Bool_Exp = {
  _and?: Array<Core_Overview_Subdomains_Bool_Exp> | null | undefined;
  _not?: Core_Overview_Subdomains_Bool_Exp | null | undefined;
  _or?: Array<Core_Overview_Subdomains_Bool_Exp> | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Constraint =
  /** unique or primary key constraint on columns "overview_id", "subdomain_id" */
  | 'core_overview_subdomains_overview_id_subdomain_id_4e2a5d3f_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_overview_subdomains_pkey';

/** input type for inserting data into table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Insert_Input = {
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  overview_id?: unknown;
  subdomain_id?: unknown;
};

/** order by max() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Max_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Min_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_overview_subdomains" */
export type Core_Overview_Subdomains_On_Conflict = {
  constraint: Core_Overview_Subdomains_Constraint;
  update_columns?: Array<Core_Overview_Subdomains_Update_Column>;
  where?: Core_Overview_Subdomains_Bool_Exp | null | undefined;
};

/** select columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'subdomain_id';

/** order by stddev() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Sum_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** update columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'subdomain_id';

/** order by var_pop() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_overview_subdomains" */
export type Core_Overview_Subdomains_Variance_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_overview" */
export type Core_Overview_Sum_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** update columns of table "core_overview" */
export type Core_Overview_Update_Column =
  /** column name */
  | 'business_impact'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'knowledge'
  /** column name */
  | 'parent_thread_id'
  /** column name */
  | 'port_service'
  /** column name */
  | 'recon_summary'
  /** column name */
  | 'rescue_count'
  /** column name */
  | 'risk_score'
  /** column name */
  | 'seed_id'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_intel'
  /** column name */
  | 'summary'
  /** column name */
  | 'target_id'
  /** column name */
  | 'tech_stack'
  /** column name */
  | 'techs'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'vuln_intel';

export type Core_Overview_Url_Results_Aggregate_Bool_Exp = {
  count?: Core_Overview_Url_Results_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Overview_Url_Results_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Overview_Url_Results_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Overview_Url_Results_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Aggregate_Order_By = {
  avg?: Core_Overview_Url_Results_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Overview_Url_Results_Max_Order_By | null | undefined;
  min?: Core_Overview_Url_Results_Min_Order_By | null | undefined;
  stddev?: Core_Overview_Url_Results_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Overview_Url_Results_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Overview_Url_Results_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Overview_Url_Results_Sum_Order_By | null | undefined;
  var_pop?: Core_Overview_Url_Results_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Overview_Url_Results_Var_Samp_Order_By | null | undefined;
  variance?: Core_Overview_Url_Results_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_overview_url_results" */
export type Core_Overview_Url_Results_Arr_Rel_Insert_Input = {
  data: Array<Core_Overview_Url_Results_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Overview_Url_Results_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Avg_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_overview_url_results". All fields are combined with a logical 'AND'. */
export type Core_Overview_Url_Results_Bool_Exp = {
  _and?: Array<Core_Overview_Url_Results_Bool_Exp> | null | undefined;
  _not?: Core_Overview_Url_Results_Bool_Exp | null | undefined;
  _or?: Array<Core_Overview_Url_Results_Bool_Exp> | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  urlresult_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_overview_url_results" */
export type Core_Overview_Url_Results_Constraint =
  /** unique or primary key constraint on columns "urlresult_id", "overview_id" */
  | 'core_overview_url_result_overview_id_urlresult_id_f1503d98_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_overview_url_results_pkey';

/** input type for inserting data into table "core_overview_url_results" */
export type Core_Overview_Url_Results_Insert_Input = {
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  overview_id?: unknown;
  urlresult_id?: unknown;
};

/** order by max() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Max_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Min_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_overview_url_results" */
export type Core_Overview_Url_Results_On_Conflict = {
  constraint: Core_Overview_Url_Results_Constraint;
  update_columns?: Array<Core_Overview_Url_Results_Update_Column>;
  where?: Core_Overview_Url_Results_Bool_Exp | null | undefined;
};

/** select columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'urlresult_id';

/** order by stddev() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Sum_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** update columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'urlresult_id';

/** order by var_pop() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_overview_url_results" */
export type Core_Overview_Url_Results_Variance_Order_By = {
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by var_pop() on columns of table "core_overview" */
export type Core_Overview_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_overview" */
export type Core_Overview_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_overview" */
export type Core_Overview_Variance_Order_By = {
  id?: Order_By | null | undefined;
  parent_thread_id?: Order_By | null | undefined;
  rescue_count?: Order_By | null | undefined;
  risk_score?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

export type Core_Payload_Aggregate_Bool_Exp = {
  count?: Core_Payload_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Payload_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Payload_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Payload_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_payload" */
export type Core_Payload_Aggregate_Order_By = {
  avg?: Core_Payload_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Payload_Max_Order_By | null | undefined;
  min?: Core_Payload_Min_Order_By | null | undefined;
  stddev?: Core_Payload_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Payload_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Payload_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Payload_Sum_Order_By | null | undefined;
  var_pop?: Core_Payload_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Payload_Var_Samp_Order_By | null | undefined;
  variance?: Core_Payload_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_payload" */
export type Core_Payload_Arr_Rel_Insert_Input = {
  data: Array<Core_Payload_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Payload_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_payload" */
export type Core_Payload_Avg_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_payload". All fields are combined with a logical 'AND'. */
export type Core_Payload_Bool_Exp = {
  _and?: Array<Core_Payload_Bool_Exp> | null | undefined;
  _not?: Core_Payload_Bool_Exp | null | undefined;
  _or?: Array<Core_Payload_Bool_Exp> | null | undefined;
  attack_vector_id?: Bigint_Comparison_Exp | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  core_attackvector?: Core_Attackvector_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  platform?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_payload" */
export type Core_Payload_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_payload_pkey';

/** input type for inserting data into table "core_payload" */
export type Core_Payload_Insert_Input = {
  attack_vector_id?: unknown;
  content?: string | null | undefined;
  core_attackvector?: Core_Attackvector_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  platform?: string | null | undefined;
};

/** order by max() on columns of table "core_payload" */
export type Core_Payload_Max_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  content?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  platform?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_payload" */
export type Core_Payload_Min_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  content?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  platform?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_payload" */
export type Core_Payload_On_Conflict = {
  constraint: Core_Payload_Constraint;
  update_columns?: Array<Core_Payload_Update_Column>;
  where?: Core_Payload_Bool_Exp | null | undefined;
};

/** select columns of table "core_payload" */
export type Core_Payload_Select_Column =
  /** column name */
  | 'attack_vector_id'
  /** column name */
  | 'content'
  /** column name */
  | 'id'
  /** column name */
  | 'platform';

/** order by stddev() on columns of table "core_payload" */
export type Core_Payload_Stddev_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_payload" */
export type Core_Payload_Stddev_Pop_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_payload" */
export type Core_Payload_Stddev_Samp_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_payload" */
export type Core_Payload_Sum_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** update columns of table "core_payload" */
export type Core_Payload_Update_Column =
  /** column name */
  | 'attack_vector_id'
  /** column name */
  | 'content'
  /** column name */
  | 'id'
  /** column name */
  | 'platform';

/** order by var_pop() on columns of table "core_payload" */
export type Core_Payload_Var_Pop_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_payload" */
export type Core_Payload_Var_Samp_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_payload" */
export type Core_Payload_Variance_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
};

export type Core_Pocrecord_Aggregate_Bool_Exp = {
  bool_and?: Core_Pocrecord_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Pocrecord_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Pocrecord_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Pocrecord_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Pocrecord_Select_Column_Core_Pocrecord_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Pocrecord_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Pocrecord_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Pocrecord_Select_Column_Core_Pocrecord_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Pocrecord_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Pocrecord_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Pocrecord_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Pocrecord_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_pocrecord" */
export type Core_Pocrecord_Aggregate_Order_By = {
  avg?: Core_Pocrecord_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Pocrecord_Max_Order_By | null | undefined;
  min?: Core_Pocrecord_Min_Order_By | null | undefined;
  stddev?: Core_Pocrecord_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Pocrecord_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Pocrecord_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Pocrecord_Sum_Order_By | null | undefined;
  var_pop?: Core_Pocrecord_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Pocrecord_Var_Samp_Order_By | null | undefined;
  variance?: Core_Pocrecord_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_pocrecord" */
export type Core_Pocrecord_Arr_Rel_Insert_Input = {
  data: Array<Core_Pocrecord_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Pocrecord_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Avg_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_pocrecord". All fields are combined with a logical 'AND'. */
export type Core_Pocrecord_Bool_Exp = {
  _and?: Array<Core_Pocrecord_Bool_Exp> | null | undefined;
  _not?: Core_Pocrecord_Bool_Exp | null | undefined;
  _or?: Array<Core_Pocrecord_Bool_Exp> | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  core_vulnerability?: Core_Vulnerability_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_verified?: Boolean_Comparison_Exp | null | undefined;
  language?: String_Comparison_Exp | null | undefined;
  result?: String_Comparison_Exp | null | undefined;
  title?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  vulnerability_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_pocrecord" */
export type Core_Pocrecord_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_pocrecord_pkey';

/** input type for inserting data into table "core_pocrecord" */
export type Core_Pocrecord_Insert_Input = {
  content?: string | null | undefined;
  core_vulnerability?: Core_Vulnerability_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  is_verified?: boolean | null | undefined;
  language?: string | null | undefined;
  result?: string | null | undefined;
  title?: string | null | undefined;
  updated_at?: unknown;
  vulnerability_id?: unknown;
};

/** order by max() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Max_Order_By = {
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  language?: Order_By | null | undefined;
  result?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Min_Order_By = {
  content?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  language?: Order_By | null | undefined;
  result?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_pocrecord" */
export type Core_Pocrecord_On_Conflict = {
  constraint: Core_Pocrecord_Constraint;
  update_columns?: Array<Core_Pocrecord_Update_Column>;
  where?: Core_Pocrecord_Bool_Exp | null | undefined;
};

/** select columns of table "core_pocrecord" */
export type Core_Pocrecord_Select_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_verified'
  /** column name */
  | 'language'
  /** column name */
  | 'result'
  /** column name */
  | 'title'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'vulnerability_id';

/** select "core_pocrecord_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_pocrecord" */
export type Core_Pocrecord_Select_Column_Core_Pocrecord_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_verified';

/** select "core_pocrecord_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_pocrecord" */
export type Core_Pocrecord_Select_Column_Core_Pocrecord_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_verified';

/** input type for updating data in table "core_pocrecord" */
export type Core_Pocrecord_Set_Input = {
  content?: string | null | undefined;
  created_at?: unknown;
  id?: unknown;
  is_verified?: boolean | null | undefined;
  language?: string | null | undefined;
  result?: string | null | undefined;
  title?: string | null | undefined;
  updated_at?: unknown;
  vulnerability_id?: unknown;
};

/** order by stddev() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Sum_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** update columns of table "core_pocrecord" */
export type Core_Pocrecord_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_verified'
  /** column name */
  | 'language'
  /** column name */
  | 'result'
  /** column name */
  | 'title'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'vulnerability_id';

/** order by var_pop() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_pocrecord" */
export type Core_Pocrecord_Variance_Order_By = {
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

export type Core_Port_Aggregate_Bool_Exp = {
  count?: Core_Port_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Port_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Port_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Port_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_port" */
export type Core_Port_Aggregate_Order_By = {
  avg?: Core_Port_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Port_Max_Order_By | null | undefined;
  min?: Core_Port_Min_Order_By | null | undefined;
  stddev?: Core_Port_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Port_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Port_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Port_Sum_Order_By | null | undefined;
  var_pop?: Core_Port_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Port_Var_Samp_Order_By | null | undefined;
  variance?: Core_Port_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_port" */
export type Core_Port_Arr_Rel_Insert_Input = {
  data: Array<Core_Port_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Port_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_port" */
export type Core_Port_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_port". All fields are combined with a logical 'AND'. */
export type Core_Port_Bool_Exp = {
  _and?: Array<Core_Port_Bool_Exp> | null | undefined;
  _not?: Core_Port_Bool_Exp | null | undefined;
  _or?: Array<Core_Port_Bool_Exp> | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_port_discovered_by_scans?: Core_Port_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_port_discovered_by_scans_aggregate?: Core_Port_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  first_seen?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  port_number?: Int_Comparison_Exp | null | undefined;
  protocol?: String_Comparison_Exp | null | undefined;
  service_name?: String_Comparison_Exp | null | undefined;
  service_version?: String_Comparison_Exp | null | undefined;
  state?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_port" */
export type Core_Port_Constraint =
  /** unique or primary key constraint on columns "protocol", "port_number", "ip_id" */
  | 'core_port_ip_id_port_number_protocol_e0db72bf_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_port_pkey';

export type Core_Port_Discovered_By_Scans_Aggregate_Bool_Exp = {
  count?: Core_Port_Discovered_By_Scans_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Port_Discovered_By_Scans_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Port_Discovered_By_Scans_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Port_Discovered_By_Scans_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "core_port_discovered_by_scans" */
export type Core_Port_Discovered_By_Scans_Arr_Rel_Insert_Input = {
  data: Array<Core_Port_Discovered_By_Scans_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Port_Discovered_By_Scans_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "core_port_discovered_by_scans". All fields are combined with a logical 'AND'. */
export type Core_Port_Discovered_By_Scans_Bool_Exp = {
  _and?: Array<Core_Port_Discovered_By_Scans_Bool_Exp> | null | undefined;
  _not?: Core_Port_Discovered_By_Scans_Bool_Exp | null | undefined;
  _or?: Array<Core_Port_Discovered_By_Scans_Bool_Exp> | null | undefined;
  core_nmapscan?: Core_Nmapscan_Bool_Exp | null | undefined;
  core_port?: Core_Port_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  nmapscan_id?: Bigint_Comparison_Exp | null | undefined;
  port_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_port_discovered_by_scans" */
export type Core_Port_Discovered_By_Scans_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_port_discovered_by_scans_pkey'
  /** unique or primary key constraint on columns "port_id", "nmapscan_id" */
  | 'core_port_discovered_by_scans_port_id_nmapscan_id_cfc7193d_uniq';

/** input type for inserting data into table "core_port_discovered_by_scans" */
export type Core_Port_Discovered_By_Scans_Insert_Input = {
  core_nmapscan?: Core_Nmapscan_Obj_Rel_Insert_Input | null | undefined;
  core_port?: Core_Port_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  nmapscan_id?: unknown;
  port_id?: unknown;
};

/** on_conflict condition type for table "core_port_discovered_by_scans" */
export type Core_Port_Discovered_By_Scans_On_Conflict = {
  constraint: Core_Port_Discovered_By_Scans_Constraint;
  update_columns?: Array<Core_Port_Discovered_By_Scans_Update_Column>;
  where?: Core_Port_Discovered_By_Scans_Bool_Exp | null | undefined;
};

/** select columns of table "core_port_discovered_by_scans" */
export type Core_Port_Discovered_By_Scans_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'nmapscan_id'
  /** column name */
  | 'port_id';

/** update columns of table "core_port_discovered_by_scans" */
export type Core_Port_Discovered_By_Scans_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'nmapscan_id'
  /** column name */
  | 'port_id';

/** input type for inserting data into table "core_port" */
export type Core_Port_Insert_Input = {
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_port_discovered_by_scans?: Core_Port_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  first_seen?: unknown;
  id?: unknown;
  ip_id?: unknown;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  last_seen?: unknown;
  port_number?: number | null | undefined;
  protocol?: string | null | undefined;
  service_name?: string | null | undefined;
  service_version?: string | null | undefined;
  state?: string | null | undefined;
};

/** order by max() on columns of table "core_port" */
export type Core_Port_Max_Order_By = {
  first_seen?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
  protocol?: Order_By | null | undefined;
  service_name?: Order_By | null | undefined;
  service_version?: Order_By | null | undefined;
  state?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_port" */
export type Core_Port_Min_Order_By = {
  first_seen?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
  protocol?: Order_By | null | undefined;
  service_name?: Order_By | null | undefined;
  service_version?: Order_By | null | undefined;
  state?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_port" */
export type Core_Port_Obj_Rel_Insert_Input = {
  data: Core_Port_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Port_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_port" */
export type Core_Port_On_Conflict = {
  constraint: Core_Port_Constraint;
  update_columns?: Array<Core_Port_Update_Column>;
  where?: Core_Port_Bool_Exp | null | undefined;
};

/** select columns of table "core_port" */
export type Core_Port_Select_Column =
  /** column name */
  | 'first_seen'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'port_number'
  /** column name */
  | 'protocol'
  /** column name */
  | 'service_name'
  /** column name */
  | 'service_version'
  /** column name */
  | 'state';

/** order by stddev() on columns of table "core_port" */
export type Core_Port_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_port" */
export type Core_Port_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_port" */
export type Core_Port_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_port" */
export type Core_Port_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** update columns of table "core_port" */
export type Core_Port_Update_Column =
  /** column name */
  | 'first_seen'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'port_number'
  /** column name */
  | 'protocol'
  /** column name */
  | 'service_name'
  /** column name */
  | 'service_version'
  /** column name */
  | 'state';

/** order by var_pop() on columns of table "core_port" */
export type Core_Port_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_port" */
export type Core_Port_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_port" */
export type Core_Port_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  port_number?: Order_By | null | undefined;
};

export type Core_Seed_Aggregate_Bool_Exp = {
  bool_and?: Core_Seed_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Seed_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Seed_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Seed_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Seed_Select_Column_Core_Seed_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Seed_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Seed_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Seed_Select_Column_Core_Seed_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Seed_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Seed_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Seed_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Seed_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_seed" */
export type Core_Seed_Aggregate_Order_By = {
  avg?: Core_Seed_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Seed_Max_Order_By | null | undefined;
  min?: Core_Seed_Min_Order_By | null | undefined;
  stddev?: Core_Seed_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Seed_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Seed_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Seed_Sum_Order_By | null | undefined;
  var_pop?: Core_Seed_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Seed_Var_Samp_Order_By | null | undefined;
  variance?: Core_Seed_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_seed" */
export type Core_Seed_Arr_Rel_Insert_Input = {
  data: Array<Core_Seed_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Seed_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_seed" */
export type Core_Seed_Avg_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_seed". All fields are combined with a logical 'AND'. */
export type Core_Seed_Bool_Exp = {
  _and?: Array<Core_Seed_Bool_Exp> | null | undefined;
  _not?: Core_Seed_Bool_Exp | null | undefined;
  _or?: Array<Core_Seed_Bool_Exp> | null | undefined;
  core_amassscans?: Core_Amassscan_Bool_Exp | null | undefined;
  core_amassscans_aggregate?: Core_Amassscan_Aggregate_Bool_Exp | null | undefined;
  core_ip_which_seeds?: Core_Ip_Which_Seed_Bool_Exp | null | undefined;
  core_ip_which_seeds_aggregate?: Core_Ip_Which_Seed_Aggregate_Bool_Exp | null | undefined;
  core_nmapscan_which_seeds?: Core_Nmapscan_Which_Seed_Bool_Exp | null | undefined;
  core_nmapscan_which_seeds_aggregate?: Core_Nmapscan_Which_Seed_Aggregate_Bool_Exp | null | undefined;
  core_overviews?: Core_Overview_Bool_Exp | null | undefined;
  core_overviews_aggregate?: Core_Overview_Aggregate_Bool_Exp | null | undefined;
  core_subdomainseeds?: Core_Subdomainseed_Bool_Exp | null | undefined;
  core_subdomainseeds_aggregate?: Core_Subdomainseed_Aggregate_Bool_Exp | null | undefined;
  core_subfinderscans?: Core_Subfinderscan_Bool_Exp | null | undefined;
  core_subfinderscans_aggregate?: Core_Subfinderscan_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_active?: Boolean_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  type?: String_Comparison_Exp | null | undefined;
  value?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_seed" */
export type Core_Seed_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_seed_pkey'
  /** unique or primary key constraint on columns "target_id", "value" */
  | 'core_seed_target_id_value_51b11daa_uniq';

/** input type for inserting data into table "core_seed" */
export type Core_Seed_Insert_Input = {
  core_amassscans?: Core_Amassscan_Arr_Rel_Insert_Input | null | undefined;
  core_ip_which_seeds?: Core_Ip_Which_Seed_Arr_Rel_Insert_Input | null | undefined;
  core_nmapscan_which_seeds?: Core_Nmapscan_Which_Seed_Arr_Rel_Insert_Input | null | undefined;
  core_overviews?: Core_Overview_Arr_Rel_Insert_Input | null | undefined;
  core_subdomainseeds?: Core_Subdomainseed_Arr_Rel_Insert_Input | null | undefined;
  core_subfinderscans?: Core_Subfinderscan_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  is_active?: boolean | null | undefined;
  target_id?: unknown;
  type?: string | null | undefined;
  value?: string | null | undefined;
};

/** order by max() on columns of table "core_seed" */
export type Core_Seed_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  type?: Order_By | null | undefined;
  value?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_seed" */
export type Core_Seed_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  type?: Order_By | null | undefined;
  value?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_seed" */
export type Core_Seed_Obj_Rel_Insert_Input = {
  data: Core_Seed_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Seed_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_seed" */
export type Core_Seed_On_Conflict = {
  constraint: Core_Seed_Constraint;
  update_columns?: Array<Core_Seed_Update_Column>;
  where?: Core_Seed_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_seed". */
export type Core_Seed_Order_By = {
  core_amassscans_aggregate?: Core_Amassscan_Aggregate_Order_By | null | undefined;
  core_ip_which_seeds_aggregate?: Core_Ip_Which_Seed_Aggregate_Order_By | null | undefined;
  core_nmapscan_which_seeds_aggregate?: Core_Nmapscan_Which_Seed_Aggregate_Order_By | null | undefined;
  core_overviews_aggregate?: Core_Overview_Aggregate_Order_By | null | undefined;
  core_subdomainseeds_aggregate?: Core_Subdomainseed_Aggregate_Order_By | null | undefined;
  core_subfinderscans_aggregate?: Core_Subfinderscan_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  is_active?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  type?: Order_By | null | undefined;
  value?: Order_By | null | undefined;
};

/** select columns of table "core_seed" */
export type Core_Seed_Select_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'target_id'
  /** column name */
  | 'type'
  /** column name */
  | 'value';

/** select "core_seed_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_seed" */
export type Core_Seed_Select_Column_Core_Seed_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_active';

/** select "core_seed_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_seed" */
export type Core_Seed_Select_Column_Core_Seed_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_active';

/** order by stddev() on columns of table "core_seed" */
export type Core_Seed_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_seed" */
export type Core_Seed_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_seed" */
export type Core_Seed_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_seed" */
export type Core_Seed_Sum_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_seed" */
export type Core_Seed_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'target_id'
  /** column name */
  | 'type'
  /** column name */
  | 'value';

/** order by var_pop() on columns of table "core_seed" */
export type Core_Seed_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_seed" */
export type Core_Seed_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_seed" */
export type Core_Seed_Variance_Order_By = {
  id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

export type Core_Subagent_Dispatch_Aggregate_Bool_Exp = {
  bool_and?: Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Subagent_Dispatch_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Subagent_Dispatch_Select_Column_Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Subagent_Dispatch_Select_Column_Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Subagent_Dispatch_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subagent_Dispatch_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Aggregate_Order_By = {
  avg?: Core_Subagent_Dispatch_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subagent_Dispatch_Max_Order_By | null | undefined;
  min?: Core_Subagent_Dispatch_Min_Order_By | null | undefined;
  stddev?: Core_Subagent_Dispatch_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subagent_Dispatch_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subagent_Dispatch_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subagent_Dispatch_Sum_Order_By | null | undefined;
  var_pop?: Core_Subagent_Dispatch_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subagent_Dispatch_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subagent_Dispatch_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Arr_Rel_Insert_Input = {
  data: Array<Core_Subagent_Dispatch_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subagent_Dispatch_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Avg_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subagent_dispatch". All fields are combined with a logical 'AND'. */
export type Core_Subagent_Dispatch_Bool_Exp = {
  _and?: Array<Core_Subagent_Dispatch_Bool_Exp> | null | undefined;
  _not?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
  _or?: Array<Core_Subagent_Dispatch_Bool_Exp> | null | undefined;
  action_id?: Bigint_Comparison_Exp | null | undefined;
  aiAssistantThreadBySubThreadId?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  dispatched_at?: Timestamptz_Comparison_Exp | null | undefined;
  dispatcher_agent?: String_Comparison_Exp | null | undefined;
  dispatcher_thread_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  objective?: String_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  result_summary?: String_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  sub_agent_type?: String_Comparison_Exp | null | undefined;
  sub_thread_id?: Bigint_Comparison_Exp | null | undefined;
  synthesized?: Boolean_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_subagent_dispatch_pkey';

/** input type for inserting data into table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Insert_Input = {
  action_id?: unknown;
  aiAssistantThreadBySubThreadId?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  completed_at?: unknown;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  dispatched_at?: unknown;
  dispatcher_agent?: string | null | undefined;
  dispatcher_thread_id?: unknown;
  id?: unknown;
  objective?: string | null | undefined;
  overview_id?: unknown;
  result_summary?: string | null | undefined;
  status?: string | null | undefined;
  sub_agent_type?: string | null | undefined;
  sub_thread_id?: unknown;
  synthesized?: boolean | null | undefined;
};

/** order by max() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Max_Order_By = {
  action_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  dispatched_at?: Order_By | null | undefined;
  dispatcher_agent?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  objective?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  result_summary?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  sub_agent_type?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Min_Order_By = {
  action_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  dispatched_at?: Order_By | null | undefined;
  dispatcher_agent?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  objective?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  result_summary?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  sub_agent_type?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_On_Conflict = {
  constraint: Core_Subagent_Dispatch_Constraint;
  update_columns?: Array<Core_Subagent_Dispatch_Update_Column>;
  where?: Core_Subagent_Dispatch_Bool_Exp | null | undefined;
};

/** select columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Select_Column =
  /** column name */
  | 'action_id'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'dispatched_at'
  /** column name */
  | 'dispatcher_agent'
  /** column name */
  | 'dispatcher_thread_id'
  /** column name */
  | 'id'
  /** column name */
  | 'objective'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'result_summary'
  /** column name */
  | 'status'
  /** column name */
  | 'sub_agent_type'
  /** column name */
  | 'sub_thread_id'
  /** column name */
  | 'synthesized';

/** select "core_subagent_dispatch_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Select_Column_Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'synthesized';

/** select "core_subagent_dispatch_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Select_Column_Core_Subagent_Dispatch_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'synthesized';

/** order by stddev() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Stddev_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Stddev_Pop_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Stddev_Samp_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Sum_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** update columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Update_Column =
  /** column name */
  | 'action_id'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'dispatched_at'
  /** column name */
  | 'dispatcher_agent'
  /** column name */
  | 'dispatcher_thread_id'
  /** column name */
  | 'id'
  /** column name */
  | 'objective'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'result_summary'
  /** column name */
  | 'status'
  /** column name */
  | 'sub_agent_type'
  /** column name */
  | 'sub_thread_id'
  /** column name */
  | 'synthesized';

/** order by var_pop() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Var_Pop_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Var_Samp_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subagent_dispatch" */
export type Core_Subagent_Dispatch_Variance_Order_By = {
  action_id?: Order_By | null | undefined;
  dispatcher_thread_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  sub_thread_id?: Order_By | null | undefined;
};

export type Core_Subbrute_Aggregate_Bool_Exp = {
  count?: Core_Subbrute_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subbrute_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subbrute_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subbrute_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subbrute" */
export type Core_Subbrute_Aggregate_Order_By = {
  avg?: Core_Subbrute_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subbrute_Max_Order_By | null | undefined;
  min?: Core_Subbrute_Min_Order_By | null | undefined;
  stddev?: Core_Subbrute_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subbrute_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subbrute_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subbrute_Sum_Order_By | null | undefined;
  var_pop?: Core_Subbrute_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subbrute_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subbrute_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subbrute" */
export type Core_Subbrute_Arr_Rel_Insert_Input = {
  data: Array<Core_Subbrute_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subbrute_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subbrute" */
export type Core_Subbrute_Avg_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subbrute". All fields are combined with a logical 'AND'. */
export type Core_Subbrute_Bool_Exp = {
  _and?: Array<Core_Subbrute_Bool_Exp> | null | undefined;
  _not?: Core_Subbrute_Bool_Exp | null | undefined;
  _or?: Array<Core_Subbrute_Bool_Exp> | null | undefined;
  added_count?: Int_Comparison_Exp | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  which_sub_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subbrute" */
export type Core_Subbrute_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_subbrute_pkey';

/** input type for inserting data into table "core_subbrute" */
export type Core_Subbrute_Insert_Input = {
  added_count?: number | null | undefined;
  completed_at?: unknown;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  started_at?: unknown;
  status?: string | null | undefined;
  which_sub_id?: unknown;
};

/** order by max() on columns of table "core_subbrute" */
export type Core_Subbrute_Max_Order_By = {
  added_count?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subbrute" */
export type Core_Subbrute_Min_Order_By = {
  added_count?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_subbrute" */
export type Core_Subbrute_On_Conflict = {
  constraint: Core_Subbrute_Constraint;
  update_columns?: Array<Core_Subbrute_Update_Column>;
  where?: Core_Subbrute_Bool_Exp | null | undefined;
};

/** select columns of table "core_subbrute" */
export type Core_Subbrute_Select_Column =
  /** column name */
  | 'added_count'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'which_sub_id';

/** order by stddev() on columns of table "core_subbrute" */
export type Core_Subbrute_Stddev_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subbrute" */
export type Core_Subbrute_Stddev_Pop_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subbrute" */
export type Core_Subbrute_Stddev_Samp_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subbrute" */
export type Core_Subbrute_Sum_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** update columns of table "core_subbrute" */
export type Core_Subbrute_Update_Column =
  /** column name */
  | 'added_count'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'which_sub_id';

/** order by var_pop() on columns of table "core_subbrute" */
export type Core_Subbrute_Var_Pop_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subbrute" */
export type Core_Subbrute_Var_Samp_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subbrute" */
export type Core_Subbrute_Variance_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_sub_id?: Order_By | null | undefined;
};

export type Core_Subdomain_Aggregate_Bool_Exp = {
  bool_and?: Core_Subdomain_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Subdomain_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Subdomain_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subdomain_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Subdomain_Select_Column_Core_Subdomain_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Subdomain_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Subdomain_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Subdomain_Select_Column_Core_Subdomain_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Subdomain_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Subdomain_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subdomain_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subdomain_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subdomain" */
export type Core_Subdomain_Aggregate_Order_By = {
  avg?: Core_Subdomain_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subdomain_Max_Order_By | null | undefined;
  min?: Core_Subdomain_Min_Order_By | null | undefined;
  stddev?: Core_Subdomain_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subdomain_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subdomain_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subdomain_Sum_Order_By | null | undefined;
  var_pop?: Core_Subdomain_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subdomain_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subdomain_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subdomain" */
export type Core_Subdomain_Arr_Rel_Insert_Input = {
  data: Array<Core_Subdomain_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subdomain_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subdomain" */
export type Core_Subdomain_Avg_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subdomain". All fields are combined with a logical 'AND'. */
export type Core_Subdomain_Bool_Exp = {
  _and?: Array<Core_Subdomain_Bool_Exp> | null | undefined;
  _not?: Core_Subdomain_Bool_Exp | null | undefined;
  _or?: Array<Core_Subdomain_Bool_Exp> | null | undefined;
  cdn_name?: String_Comparison_Exp | null | undefined;
  core_analyzedata?: Core_Analyzedata_Bool_Exp | null | undefined;
  core_analyzedata_aggregate?: Core_Analyzedata_Aggregate_Bool_Exp | null | undefined;
  core_dnsrecords?: Core_Dnsrecord_Bool_Exp | null | undefined;
  core_dnsrecords_aggregate?: Core_Dnsrecord_Aggregate_Bool_Exp | null | undefined;
  core_endpoint_related_subdomains?: Core_Endpoint_Related_Subdomains_Bool_Exp | null | undefined;
  core_endpoint_related_subdomains_aggregate?: Core_Endpoint_Related_Subdomains_Aggregate_Bool_Exp | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Bool_Exp | null | undefined;
  core_nucleiscans?: Core_Nucleiscan_Bool_Exp | null | undefined;
  core_nucleiscans_aggregate?: Core_Nucleiscan_Aggregate_Bool_Exp | null | undefined;
  core_overview_subdomains?: Core_Overview_Subdomains_Bool_Exp | null | undefined;
  core_overview_subdomains_aggregate?: Core_Overview_Subdomains_Aggregate_Bool_Exp | null | undefined;
  core_subbrutes?: Core_Subbrute_Bool_Exp | null | undefined;
  core_subbrutes_aggregate?: Core_Subbrute_Aggregate_Bool_Exp | null | undefined;
  core_subdomain_discovered_by_scans?: Core_Subdomain_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_subdomain_discovered_by_scans_aggregate?: Core_Subdomain_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  core_subdomain_ips?: Core_Subdomain_Ips_Bool_Exp | null | undefined;
  core_subdomain_ips_aggregate?: Core_Subdomain_Ips_Aggregate_Bool_Exp | null | undefined;
  core_subdomainseeds?: Core_Subdomainseed_Bool_Exp | null | undefined;
  core_subdomainseeds_aggregate?: Core_Subdomainseed_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_techstacks?: Core_Techstack_Bool_Exp | null | undefined;
  core_techstacks_aggregate?: Core_Techstack_Aggregate_Bool_Exp | null | undefined;
  core_urlresult_related_subdomains?: Core_Urlresult_Related_Subdomains_Bool_Exp | null | undefined;
  core_urlresult_related_subdomains_aggregate?: Core_Urlresult_Related_Subdomains_Aggregate_Bool_Exp | null | undefined;
  core_urlscans?: Core_Urlscan_Bool_Exp | null | undefined;
  core_urlscans_aggregate?: Core_Urlscan_Aggregate_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  first_seen?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_active?: Boolean_Comparison_Exp | null | undefined;
  is_cdn?: Boolean_Comparison_Exp | null | undefined;
  is_resolvable?: Boolean_Comparison_Exp | null | undefined;
  is_tech_analyzed?: Boolean_Comparison_Exp | null | undefined;
  is_waf?: Boolean_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  sources_text?: String_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  waf_name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subdomain" */
export type Core_Subdomain_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_subdomain_pkey';

export type Core_Subdomain_Discovered_By_Scans_Aggregate_Bool_Exp = {
  count?: Core_Subdomain_Discovered_By_Scans_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subdomain_Discovered_By_Scans_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subdomain_Discovered_By_Scans_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subdomain_Discovered_By_Scans_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Aggregate_Order_By = {
  avg?: Core_Subdomain_Discovered_By_Scans_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subdomain_Discovered_By_Scans_Max_Order_By | null | undefined;
  min?: Core_Subdomain_Discovered_By_Scans_Min_Order_By | null | undefined;
  stddev?: Core_Subdomain_Discovered_By_Scans_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subdomain_Discovered_By_Scans_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subdomain_Discovered_By_Scans_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subdomain_Discovered_By_Scans_Sum_Order_By | null | undefined;
  var_pop?: Core_Subdomain_Discovered_By_Scans_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subdomain_Discovered_By_Scans_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subdomain_Discovered_By_Scans_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Arr_Rel_Insert_Input = {
  data: Array<Core_Subdomain_Discovered_By_Scans_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subdomain_Discovered_By_Scans_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Avg_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subdomain_discovered_by_scans". All fields are combined with a logical 'AND'. */
export type Core_Subdomain_Discovered_By_Scans_Bool_Exp = {
  _and?: Array<Core_Subdomain_Discovered_By_Scans_Bool_Exp> | null | undefined;
  _not?: Core_Subdomain_Discovered_By_Scans_Bool_Exp | null | undefined;
  _or?: Array<Core_Subdomain_Discovered_By_Scans_Bool_Exp> | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_subfinderscan?: Core_Subfinderscan_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  subfinderscan_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Constraint =
  /** unique or primary key constraint on columns "subfinderscan_id", "subdomain_id" */
  | 'core_subdomain_discovere_subdomain_id_subfindersc_bb1dba8b_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_subdomain_discovered_by_scans_pkey';

/** input type for inserting data into table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Insert_Input = {
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_subfinderscan?: Core_Subfinderscan_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  subdomain_id?: unknown;
  subfinderscan_id?: unknown;
};

/** order by max() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Max_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Min_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_On_Conflict = {
  constraint: Core_Subdomain_Discovered_By_Scans_Constraint;
  update_columns?: Array<Core_Subdomain_Discovered_By_Scans_Update_Column>;
  where?: Core_Subdomain_Discovered_By_Scans_Bool_Exp | null | undefined;
};

/** select columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'subfinderscan_id';

/** order by stddev() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Sum_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** update columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'subfinderscan_id';

/** order by var_pop() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subdomain_discovered_by_scans" */
export type Core_Subdomain_Discovered_By_Scans_Variance_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  subfinderscan_id?: Order_By | null | undefined;
};

/** input type for inserting data into table "core_subdomain" */
export type Core_Subdomain_Insert_Input = {
  cdn_name?: string | null | undefined;
  core_analyzedata?: Core_Analyzedata_Arr_Rel_Insert_Input | null | undefined;
  core_dnsrecords?: Core_Dnsrecord_Arr_Rel_Insert_Input | null | undefined;
  core_endpoint_related_subdomains?: Core_Endpoint_Related_Subdomains_Arr_Rel_Insert_Input | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Arr_Rel_Insert_Input | null | undefined;
  core_nucleiscans?: Core_Nucleiscan_Arr_Rel_Insert_Input | null | undefined;
  core_overview_subdomains?: Core_Overview_Subdomains_Arr_Rel_Insert_Input | null | undefined;
  core_subbrutes?: Core_Subbrute_Arr_Rel_Insert_Input | null | undefined;
  core_subdomain_discovered_by_scans?: Core_Subdomain_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  core_subdomain_ips?: Core_Subdomain_Ips_Arr_Rel_Insert_Input | null | undefined;
  core_subdomainseeds?: Core_Subdomainseed_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_techstacks?: Core_Techstack_Arr_Rel_Insert_Input | null | undefined;
  core_urlresult_related_subdomains?: Core_Urlresult_Related_Subdomains_Arr_Rel_Insert_Input | null | undefined;
  core_urlscans?: Core_Urlscan_Arr_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  first_seen?: unknown;
  id?: unknown;
  is_active?: boolean | null | undefined;
  is_cdn?: boolean | null | undefined;
  is_resolvable?: boolean | null | undefined;
  is_tech_analyzed?: boolean | null | undefined;
  is_waf?: boolean | null | undefined;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  last_seen?: unknown;
  name?: string | null | undefined;
  sources_text?: string | null | undefined;
  target_id?: unknown;
  waf_name?: string | null | undefined;
};

export type Core_Subdomain_Ips_Aggregate_Bool_Exp = {
  count?: Core_Subdomain_Ips_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subdomain_Ips_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subdomain_Ips_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subdomain_Ips_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Aggregate_Order_By = {
  avg?: Core_Subdomain_Ips_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subdomain_Ips_Max_Order_By | null | undefined;
  min?: Core_Subdomain_Ips_Min_Order_By | null | undefined;
  stddev?: Core_Subdomain_Ips_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subdomain_Ips_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subdomain_Ips_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subdomain_Ips_Sum_Order_By | null | undefined;
  var_pop?: Core_Subdomain_Ips_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subdomain_Ips_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subdomain_Ips_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Arr_Rel_Insert_Input = {
  data: Array<Core_Subdomain_Ips_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subdomain_Ips_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Avg_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subdomain_ips". All fields are combined with a logical 'AND'. */
export type Core_Subdomain_Ips_Bool_Exp = {
  _and?: Array<Core_Subdomain_Ips_Bool_Exp> | null | undefined;
  _not?: Core_Subdomain_Ips_Bool_Exp | null | undefined;
  _or?: Array<Core_Subdomain_Ips_Bool_Exp> | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_id?: Bigint_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_subdomain_ips_pkey'
  /** unique or primary key constraint on columns "subdomain_id", "ip_id" */
  | 'core_subdomain_ips_subdomain_id_ip_id_be0706f2_uniq';

/** input type for inserting data into table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Insert_Input = {
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  ip_id?: unknown;
  subdomain_id?: unknown;
};

/** order by max() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Max_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Min_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_subdomain_ips" */
export type Core_Subdomain_Ips_On_Conflict = {
  constraint: Core_Subdomain_Ips_Constraint;
  update_columns?: Array<Core_Subdomain_Ips_Update_Column>;
  where?: Core_Subdomain_Ips_Bool_Exp | null | undefined;
};

/** select columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'subdomain_id';

/** order by stddev() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Sum_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** update columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'ip_id'
  /** column name */
  | 'subdomain_id';

/** order by var_pop() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subdomain_ips" */
export type Core_Subdomain_Ips_Variance_Order_By = {
  id?: Order_By | null | undefined;
  ip_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by max() on columns of table "core_subdomain" */
export type Core_Subdomain_Max_Order_By = {
  cdn_name?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  first_seen?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  sources_text?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  waf_name?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subdomain" */
export type Core_Subdomain_Min_Order_By = {
  cdn_name?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  first_seen?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  sources_text?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  waf_name?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_subdomain" */
export type Core_Subdomain_Obj_Rel_Insert_Input = {
  data: Core_Subdomain_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Subdomain_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_subdomain" */
export type Core_Subdomain_On_Conflict = {
  constraint: Core_Subdomain_Constraint;
  update_columns?: Array<Core_Subdomain_Update_Column>;
  where?: Core_Subdomain_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_subdomain". */
export type Core_Subdomain_Order_By = {
  cdn_name?: Order_By | null | undefined;
  core_analyzedata_aggregate?: Core_Analyzedata_Aggregate_Order_By | null | undefined;
  core_dnsrecords_aggregate?: Core_Dnsrecord_Aggregate_Order_By | null | undefined;
  core_endpoint_related_subdomains_aggregate?: Core_Endpoint_Related_Subdomains_Aggregate_Order_By | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Order_By | null | undefined;
  core_nucleiscans_aggregate?: Core_Nucleiscan_Aggregate_Order_By | null | undefined;
  core_overview_subdomains_aggregate?: Core_Overview_Subdomains_Aggregate_Order_By | null | undefined;
  core_subbrutes_aggregate?: Core_Subbrute_Aggregate_Order_By | null | undefined;
  core_subdomain_discovered_by_scans_aggregate?: Core_Subdomain_Discovered_By_Scans_Aggregate_Order_By | null | undefined;
  core_subdomain_ips_aggregate?: Core_Subdomain_Ips_Aggregate_Order_By | null | undefined;
  core_subdomainseeds_aggregate?: Core_Subdomainseed_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  core_techstacks_aggregate?: Core_Techstack_Aggregate_Order_By | null | undefined;
  core_urlresult_related_subdomains_aggregate?: Core_Urlresult_Related_Subdomains_Aggregate_Order_By | null | undefined;
  core_urlscans_aggregate?: Core_Urlscan_Aggregate_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  first_seen?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  is_active?: Order_By | null | undefined;
  is_cdn?: Order_By | null | undefined;
  is_resolvable?: Order_By | null | undefined;
  is_tech_analyzed?: Order_By | null | undefined;
  is_waf?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  sources_text?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  waf_name?: Order_By | null | undefined;
};

/** select columns of table "core_subdomain" */
export type Core_Subdomain_Select_Column =
  /** column name */
  | 'cdn_name'
  /** column name */
  | 'created_at'
  /** column name */
  | 'first_seen'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'name'
  /** column name */
  | 'sources_text'
  /** column name */
  | 'target_id'
  /** column name */
  | 'waf_name';

/** select "core_subdomain_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_subdomain" */
export type Core_Subdomain_Select_Column_Core_Subdomain_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf';

/** select "core_subdomain_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_subdomain" */
export type Core_Subdomain_Select_Column_Core_Subdomain_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf';

/** order by stddev() on columns of table "core_subdomain" */
export type Core_Subdomain_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subdomain" */
export type Core_Subdomain_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subdomain" */
export type Core_Subdomain_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subdomain" */
export type Core_Subdomain_Sum_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_subdomain" */
export type Core_Subdomain_Update_Column =
  /** column name */
  | 'cdn_name'
  /** column name */
  | 'created_at'
  /** column name */
  | 'first_seen'
  /** column name */
  | 'id'
  /** column name */
  | 'is_active'
  /** column name */
  | 'is_cdn'
  /** column name */
  | 'is_resolvable'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'is_waf'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'name'
  /** column name */
  | 'sources_text'
  /** column name */
  | 'target_id'
  /** column name */
  | 'waf_name';

/** order by var_pop() on columns of table "core_subdomain" */
export type Core_Subdomain_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subdomain" */
export type Core_Subdomain_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subdomain" */
export type Core_Subdomain_Variance_Order_By = {
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

export type Core_Subdomainseed_Aggregate_Bool_Exp = {
  count?: Core_Subdomainseed_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subdomainseed_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subdomainseed_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subdomainseed_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subdomainseed" */
export type Core_Subdomainseed_Aggregate_Order_By = {
  avg?: Core_Subdomainseed_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subdomainseed_Max_Order_By | null | undefined;
  min?: Core_Subdomainseed_Min_Order_By | null | undefined;
  stddev?: Core_Subdomainseed_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subdomainseed_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subdomainseed_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subdomainseed_Sum_Order_By | null | undefined;
  var_pop?: Core_Subdomainseed_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subdomainseed_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subdomainseed_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subdomainseed" */
export type Core_Subdomainseed_Arr_Rel_Insert_Input = {
  data: Array<Core_Subdomainseed_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subdomainseed_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Avg_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subdomainseed". All fields are combined with a logical 'AND'. */
export type Core_Subdomainseed_Bool_Exp = {
  _and?: Array<Core_Subdomainseed_Bool_Exp> | null | undefined;
  _not?: Core_Subdomainseed_Bool_Exp | null | undefined;
  _or?: Array<Core_Subdomainseed_Bool_Exp> | null | undefined;
  core_seed?: Core_Seed_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  seed_id?: Bigint_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subdomainseed" */
export type Core_Subdomainseed_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_subdomainseed_pkey'
  /** unique or primary key constraint on columns "subdomain_id", "seed_id" */
  | 'core_subdomainseed_subdomain_id_seed_id_a7ff889b_uniq';

/** input type for inserting data into table "core_subdomainseed" */
export type Core_Subdomainseed_Insert_Input = {
  core_seed?: Core_Seed_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  id?: unknown;
  seed_id?: unknown;
  subdomain_id?: unknown;
};

/** order by max() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Max_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Min_Order_By = {
  created_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_subdomainseed" */
export type Core_Subdomainseed_On_Conflict = {
  constraint: Core_Subdomainseed_Constraint;
  update_columns?: Array<Core_Subdomainseed_Update_Column>;
  where?: Core_Subdomainseed_Bool_Exp | null | undefined;
};

/** select columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Select_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'seed_id'
  /** column name */
  | 'subdomain_id';

/** order by stddev() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Sum_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** update columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'id'
  /** column name */
  | 'seed_id'
  /** column name */
  | 'subdomain_id';

/** order by var_pop() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subdomainseed" */
export type Core_Subdomainseed_Variance_Order_By = {
  id?: Order_By | null | undefined;
  seed_id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
};

export type Core_Subfinderscan_Aggregate_Bool_Exp = {
  count?: Core_Subfinderscan_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Subfinderscan_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Subfinderscan_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Subfinderscan_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_subfinderscan" */
export type Core_Subfinderscan_Aggregate_Order_By = {
  avg?: Core_Subfinderscan_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Subfinderscan_Max_Order_By | null | undefined;
  min?: Core_Subfinderscan_Min_Order_By | null | undefined;
  stddev?: Core_Subfinderscan_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Subfinderscan_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Subfinderscan_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Subfinderscan_Sum_Order_By | null | undefined;
  var_pop?: Core_Subfinderscan_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Subfinderscan_Var_Samp_Order_By | null | undefined;
  variance?: Core_Subfinderscan_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_subfinderscan" */
export type Core_Subfinderscan_Arr_Rel_Insert_Input = {
  data: Array<Core_Subfinderscan_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Subfinderscan_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Avg_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_subfinderscan". All fields are combined with a logical 'AND'. */
export type Core_Subfinderscan_Bool_Exp = {
  _and?: Array<Core_Subfinderscan_Bool_Exp> | null | undefined;
  _not?: Core_Subfinderscan_Bool_Exp | null | undefined;
  _or?: Array<Core_Subfinderscan_Bool_Exp> | null | undefined;
  added_count?: Int_Comparison_Exp | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_seed?: Core_Seed_Bool_Exp | null | undefined;
  core_subdomain_discovered_by_scans?: Core_Subdomain_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_subdomain_discovered_by_scans_aggregate?: Core_Subdomain_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  which_seed_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_subfinderscan" */
export type Core_Subfinderscan_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_subfinderscan_pkey';

/** input type for inserting data into table "core_subfinderscan" */
export type Core_Subfinderscan_Insert_Input = {
  added_count?: number | null | undefined;
  completed_at?: unknown;
  core_seed?: Core_Seed_Obj_Rel_Insert_Input | null | undefined;
  core_subdomain_discovered_by_scans?: Core_Subdomain_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  started_at?: unknown;
  status?: string | null | undefined;
  which_seed_id?: unknown;
};

/** order by max() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Max_Order_By = {
  added_count?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Min_Order_By = {
  added_count?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_subfinderscan" */
export type Core_Subfinderscan_Obj_Rel_Insert_Input = {
  data: Core_Subfinderscan_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Subfinderscan_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_subfinderscan" */
export type Core_Subfinderscan_On_Conflict = {
  constraint: Core_Subfinderscan_Constraint;
  update_columns?: Array<Core_Subfinderscan_Update_Column>;
  where?: Core_Subfinderscan_Bool_Exp | null | undefined;
};

/** select columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Select_Column =
  /** column name */
  | 'added_count'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'which_seed_id';

/** order by stddev() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Stddev_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Stddev_Pop_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Stddev_Samp_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Sum_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** update columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Update_Column =
  /** column name */
  | 'added_count'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'which_seed_id';

/** order by var_pop() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Var_Pop_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Var_Samp_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_subfinderscan" */
export type Core_Subfinderscan_Variance_Order_By = {
  added_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  which_seed_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_target". All fields are combined with a logical 'AND'. */
export type Core_Target_Bool_Exp = {
  _and?: Array<Core_Target_Bool_Exp> | null | undefined;
  _not?: Core_Target_Bool_Exp | null | undefined;
  _or?: Array<Core_Target_Bool_Exp> | null | undefined;
  ai_assistant_threads?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  ai_assistant_threads_aggregate?: Ai_Assistant_Thread_Aggregate_Bool_Exp | null | undefined;
  core_amassscans?: Core_Amassscan_Bool_Exp | null | undefined;
  core_amassscans_aggregate?: Core_Amassscan_Aggregate_Bool_Exp | null | undefined;
  core_endpoints?: Core_Endpoint_Bool_Exp | null | undefined;
  core_endpoints_aggregate?: Core_Endpoint_Aggregate_Bool_Exp | null | undefined;
  core_ips?: Core_Ip_Bool_Exp | null | undefined;
  core_ips_aggregate?: Core_Ip_Aggregate_Bool_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_overviews?: Core_Overview_Bool_Exp | null | undefined;
  core_overviews_aggregate?: Core_Overview_Aggregate_Bool_Exp | null | undefined;
  core_seeds?: Core_Seed_Bool_Exp | null | undefined;
  core_seeds_aggregate?: Core_Seed_Aggregate_Bool_Exp | null | undefined;
  core_subdomains?: Core_Subdomain_Bool_Exp | null | undefined;
  core_subdomains_aggregate?: Core_Subdomain_Aggregate_Bool_Exp | null | undefined;
  core_targetrequestconfig?: Core_Targetrequestconfig_Bool_Exp | null | undefined;
  core_techstacks?: Core_Techstack_Bool_Exp | null | undefined;
  core_techstacks_aggregate?: Core_Techstack_Aggregate_Bool_Exp | null | undefined;
  core_urlresults?: Core_Urlresult_Bool_Exp | null | undefined;
  core_urlresults_aggregate?: Core_Urlresult_Aggregate_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  description?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_target" */
export type Core_Target_Constraint =
  /** unique or primary key constraint on columns "name" */
  | 'core_target_name_key'
  /** unique or primary key constraint on columns "id" */
  | 'core_target_pkey';

/** input type for inserting data into table "core_target" */
export type Core_Target_Insert_Input = {
  ai_assistant_threads?: Ai_Assistant_Thread_Arr_Rel_Insert_Input | null | undefined;
  core_amassscans?: Core_Amassscan_Arr_Rel_Insert_Input | null | undefined;
  core_endpoints?: Core_Endpoint_Arr_Rel_Insert_Input | null | undefined;
  core_ips?: Core_Ip_Arr_Rel_Insert_Input | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_overviews?: Core_Overview_Arr_Rel_Insert_Input | null | undefined;
  core_seeds?: Core_Seed_Arr_Rel_Insert_Input | null | undefined;
  core_subdomains?: Core_Subdomain_Arr_Rel_Insert_Input | null | undefined;
  core_targetrequestconfig?: Core_Targetrequestconfig_Obj_Rel_Insert_Input | null | undefined;
  core_techstacks?: Core_Techstack_Arr_Rel_Insert_Input | null | undefined;
  core_urlresults?: Core_Urlresult_Arr_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  description?: string | null | undefined;
  id?: unknown;
  name?: string | null | undefined;
};

/** input type for inserting object relation for remote table "core_target" */
export type Core_Target_Obj_Rel_Insert_Input = {
  data: Core_Target_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Target_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_target" */
export type Core_Target_On_Conflict = {
  constraint: Core_Target_Constraint;
  update_columns?: Array<Core_Target_Update_Column>;
  where?: Core_Target_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_target". */
export type Core_Target_Order_By = {
  ai_assistant_threads_aggregate?: Ai_Assistant_Thread_Aggregate_Order_By | null | undefined;
  core_amassscans_aggregate?: Core_Amassscan_Aggregate_Order_By | null | undefined;
  core_endpoints_aggregate?: Core_Endpoint_Aggregate_Order_By | null | undefined;
  core_ips_aggregate?: Core_Ip_Aggregate_Order_By | null | undefined;
  core_overview?: Core_Overview_Order_By | null | undefined;
  core_overviews_aggregate?: Core_Overview_Aggregate_Order_By | null | undefined;
  core_seeds_aggregate?: Core_Seed_Aggregate_Order_By | null | undefined;
  core_subdomains_aggregate?: Core_Subdomain_Aggregate_Order_By | null | undefined;
  core_targetrequestconfig?: Core_Targetrequestconfig_Order_By | null | undefined;
  core_techstacks_aggregate?: Core_Techstack_Aggregate_Order_By | null | undefined;
  core_urlresults_aggregate?: Core_Urlresult_Aggregate_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
};

/** input type for updating data in table "core_target" */
export type Core_Target_Set_Input = {
  created_at?: unknown;
  description?: string | null | undefined;
  id?: unknown;
  name?: string | null | undefined;
};

/** update columns of table "core_target" */
export type Core_Target_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'description'
  /** column name */
  | 'id'
  /** column name */
  | 'name';

/** Boolean expression to filter rows from the table "core_targetrequestconfig". All fields are combined with a logical 'AND'. */
export type Core_Targetrequestconfig_Bool_Exp = {
  _and?: Array<Core_Targetrequestconfig_Bool_Exp> | null | undefined;
  _not?: Core_Targetrequestconfig_Bool_Exp | null | undefined;
  _or?: Array<Core_Targetrequestconfig_Bool_Exp> | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  custom_headers?: Jsonb_Comparison_Exp | null | undefined;
  header_enabled?: Boolean_Comparison_Exp | null | undefined;
  header_prefix?: String_Comparison_Exp | null | undefined;
  header_username?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  max_concurrency?: Int_Comparison_Exp | null | undefined;
  rps?: Int_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  timeout?: Int_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_targetrequestconfig" */
export type Core_Targetrequestconfig_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_targetrequestconfig_pkey'
  /** unique or primary key constraint on columns "target_id" */
  | 'core_targetrequestconfig_target_id_key';

/** input type for inserting data into table "core_targetrequestconfig" */
export type Core_Targetrequestconfig_Insert_Input = {
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  custom_headers?: unknown;
  header_enabled?: boolean | null | undefined;
  header_prefix?: string | null | undefined;
  header_username?: string | null | undefined;
  id?: unknown;
  max_concurrency?: number | null | undefined;
  rps?: number | null | undefined;
  target_id?: unknown;
  timeout?: number | null | undefined;
  updated_at?: unknown;
};

/** input type for inserting object relation for remote table "core_targetrequestconfig" */
export type Core_Targetrequestconfig_Obj_Rel_Insert_Input = {
  data: Core_Targetrequestconfig_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Targetrequestconfig_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_targetrequestconfig" */
export type Core_Targetrequestconfig_On_Conflict = {
  constraint: Core_Targetrequestconfig_Constraint;
  update_columns?: Array<Core_Targetrequestconfig_Update_Column>;
  where?: Core_Targetrequestconfig_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_targetrequestconfig". */
export type Core_Targetrequestconfig_Order_By = {
  core_target?: Core_Target_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  custom_headers?: Order_By | null | undefined;
  header_enabled?: Order_By | null | undefined;
  header_prefix?: Order_By | null | undefined;
  header_username?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  max_concurrency?: Order_By | null | undefined;
  rps?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  timeout?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** update columns of table "core_targetrequestconfig" */
export type Core_Targetrequestconfig_Update_Column =
  /** column name */
  | 'created_at'
  /** column name */
  | 'custom_headers'
  /** column name */
  | 'header_enabled'
  /** column name */
  | 'header_prefix'
  /** column name */
  | 'header_username'
  /** column name */
  | 'id'
  /** column name */
  | 'max_concurrency'
  /** column name */
  | 'rps'
  /** column name */
  | 'target_id'
  /** column name */
  | 'timeout'
  /** column name */
  | 'updated_at';

export type Core_Techstack_Aggregate_Bool_Exp = {
  count?: Core_Techstack_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Techstack_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Techstack_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstack_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_techstack" */
export type Core_Techstack_Aggregate_Order_By = {
  avg?: Core_Techstack_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Techstack_Max_Order_By | null | undefined;
  min?: Core_Techstack_Min_Order_By | null | undefined;
  stddev?: Core_Techstack_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Techstack_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Techstack_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Techstack_Sum_Order_By | null | undefined;
  var_pop?: Core_Techstack_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Techstack_Var_Samp_Order_By | null | undefined;
  variance?: Core_Techstack_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_techstack" */
export type Core_Techstack_Arr_Rel_Insert_Input = {
  data: Array<Core_Techstack_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Techstack_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_techstack" */
export type Core_Techstack_Avg_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_techstack". All fields are combined with a logical 'AND'. */
export type Core_Techstack_Bool_Exp = {
  _and?: Array<Core_Techstack_Bool_Exp> | null | undefined;
  _not?: Core_Techstack_Bool_Exp | null | undefined;
  _or?: Array<Core_Techstack_Bool_Exp> | null | undefined;
  categories?: Jsonb_Comparison_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_techstackcvemappings?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  core_techstackcvemappings_aggregate?: Core_Techstackcvemapping_Aggregate_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  version?: String_Comparison_Exp | null | undefined;
  which_url_result_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_techstack" */
export type Core_Techstack_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_techstack_pkey';

/** input type for inserting data into table "core_techstack" */
export type Core_Techstack_Insert_Input = {
  categories?: unknown;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_techstackcvemappings?: Core_Techstackcvemapping_Arr_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  last_seen?: unknown;
  name?: string | null | undefined;
  subdomain_id?: unknown;
  target_id?: unknown;
  version?: string | null | undefined;
  which_url_result_id?: unknown;
};

/** order by max() on columns of table "core_techstack" */
export type Core_Techstack_Max_Order_By = {
  id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_techstack" */
export type Core_Techstack_Min_Order_By = {
  id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  version?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_techstack" */
export type Core_Techstack_Obj_Rel_Insert_Input = {
  data: Core_Techstack_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Techstack_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_techstack" */
export type Core_Techstack_On_Conflict = {
  constraint: Core_Techstack_Constraint;
  update_columns?: Array<Core_Techstack_Update_Column>;
  where?: Core_Techstack_Bool_Exp | null | undefined;
};

/** select columns of table "core_techstack" */
export type Core_Techstack_Select_Column =
  /** column name */
  | 'categories'
  /** column name */
  | 'id'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'name'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'target_id'
  /** column name */
  | 'version'
  /** column name */
  | 'which_url_result_id';

/** order by stddev() on columns of table "core_techstack" */
export type Core_Techstack_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_techstack" */
export type Core_Techstack_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_techstack" */
export type Core_Techstack_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_techstack" */
export type Core_Techstack_Sum_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** update columns of table "core_techstack" */
export type Core_Techstack_Update_Column =
  /** column name */
  | 'categories'
  /** column name */
  | 'id'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'name'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'target_id'
  /** column name */
  | 'version'
  /** column name */
  | 'which_url_result_id';

/** order by var_pop() on columns of table "core_techstack" */
export type Core_Techstack_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_techstack" */
export type Core_Techstack_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_techstack" */
export type Core_Techstack_Variance_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  which_url_result_id?: Order_By | null | undefined;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp = {
  avg?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Avg | null | undefined;
  bool_and?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  corr?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr | null | undefined;
  count?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Count | null | undefined;
  covar_samp?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp | null | undefined;
  max?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Max | null | undefined;
  min?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Min | null | undefined;
  stddev_samp?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Stddev_Samp | null | undefined;
  sum?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Sum | null | undefined;
  var_samp?: Core_Techstackcvemapping_Aggregate_Bool_Exp_Var_Samp | null | undefined;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Avg = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Avg_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr = {
  arguments: Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr_Arguments;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr_Arguments = {
  X: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr_Arguments_Columns;
  Y: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr_Arguments_Columns;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Techstackcvemapping_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp = {
  arguments: Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp_Arguments;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp_Arguments = {
  X: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns;
  Y: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Max = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Max_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Min = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Min_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Stddev_Samp = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Stddev_Samp_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Sum = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Sum_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

export type Core_Techstackcvemapping_Aggregate_Bool_Exp_Var_Samp = {
  arguments: Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Var_Samp_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  predicate: Float8_Comparison_Exp;
};

/** order by aggregate values of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Aggregate_Order_By = {
  avg?: Core_Techstackcvemapping_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Techstackcvemapping_Max_Order_By | null | undefined;
  min?: Core_Techstackcvemapping_Min_Order_By | null | undefined;
  stddev?: Core_Techstackcvemapping_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Techstackcvemapping_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Techstackcvemapping_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Techstackcvemapping_Sum_Order_By | null | undefined;
  var_pop?: Core_Techstackcvemapping_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Techstackcvemapping_Var_Samp_Order_By | null | undefined;
  variance?: Core_Techstackcvemapping_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Arr_Rel_Insert_Input = {
  data: Array<Core_Techstackcvemapping_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Techstackcvemapping_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Avg_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_techstackcvemapping". All fields are combined with a logical 'AND'. */
export type Core_Techstackcvemapping_Bool_Exp = {
  _and?: Array<Core_Techstackcvemapping_Bool_Exp> | null | undefined;
  _not?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
  _or?: Array<Core_Techstackcvemapping_Bool_Exp> | null | undefined;
  confidence?: Float8_Comparison_Exp | null | undefined;
  core_cveintelligence?: Core_Cveintelligence_Bool_Exp | null | undefined;
  core_techstack?: Core_Techstack_Bool_Exp | null | undefined;
  cve_intelligence_id?: Bigint_Comparison_Exp | null | undefined;
  discovered_at?: Timestamptz_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  notified?: Boolean_Comparison_Exp | null | undefined;
  techstack_id?: Bigint_Comparison_Exp | null | undefined;
  version_match?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_techstackcvemapping_pkey'
  /** unique or primary key constraint on columns "cve_intelligence_id", "techstack_id" */
  | 'core_techstackcvemapping_techstack_id_cve_intelli_fc7d42dd_uniq';

/** input type for inserting data into table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Insert_Input = {
  confidence?: unknown;
  core_cveintelligence?: Core_Cveintelligence_Obj_Rel_Insert_Input | null | undefined;
  core_techstack?: Core_Techstack_Obj_Rel_Insert_Input | null | undefined;
  cve_intelligence_id?: unknown;
  discovered_at?: unknown;
  id?: unknown;
  notified?: boolean | null | undefined;
  techstack_id?: unknown;
  version_match?: string | null | undefined;
};

/** order by max() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Max_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  discovered_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
  version_match?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Min_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  discovered_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
  version_match?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_On_Conflict = {
  constraint: Core_Techstackcvemapping_Constraint;
  update_columns?: Array<Core_Techstackcvemapping_Update_Column>;
  where?: Core_Techstackcvemapping_Bool_Exp | null | undefined;
};

/** select columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column =
  /** column name */
  | 'confidence'
  /** column name */
  | 'cve_intelligence_id'
  /** column name */
  | 'discovered_at'
  /** column name */
  | 'id'
  /** column name */
  | 'notified'
  /** column name */
  | 'techstack_id'
  /** column name */
  | 'version_match';

/** select "core_techstackcvemapping_aggregate_bool_exp_avg_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Avg_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'notified';

/** select "core_techstackcvemapping_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'notified';

/** select "core_techstackcvemapping_aggregate_bool_exp_corr_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Corr_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_covar_samp_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Covar_Samp_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_max_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Max_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_min_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Min_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_stddev_samp_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Stddev_Samp_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_sum_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Sum_Arguments_Columns =
  /** column name */
  | 'confidence';

/** select "core_techstackcvemapping_aggregate_bool_exp_var_samp_arguments_columns" columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Select_Column_Core_Techstackcvemapping_Aggregate_Bool_Exp_Var_Samp_Arguments_Columns =
  /** column name */
  | 'confidence';

/** order by stddev() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Stddev_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Stddev_Pop_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Stddev_Samp_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Sum_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** update columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Update_Column =
  /** column name */
  | 'confidence'
  /** column name */
  | 'cve_intelligence_id'
  /** column name */
  | 'discovered_at'
  /** column name */
  | 'id'
  /** column name */
  | 'notified'
  /** column name */
  | 'techstack_id'
  /** column name */
  | 'version_match';

/** order by var_pop() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Var_Pop_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Var_Samp_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_techstackcvemapping" */
export type Core_Techstackcvemapping_Variance_Order_By = {
  confidence?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  techstack_id?: Order_By | null | undefined;
};

export type Core_Urlparameter_Aggregate_Bool_Exp = {
  count?: Core_Urlparameter_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Urlparameter_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Urlparameter_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlparameter_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "core_urlparameter" */
export type Core_Urlparameter_Arr_Rel_Insert_Input = {
  data: Array<Core_Urlparameter_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Urlparameter_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "core_urlparameter". All fields are combined with a logical 'AND'. */
export type Core_Urlparameter_Bool_Exp = {
  _and?: Array<Core_Urlparameter_Bool_Exp> | null | undefined;
  _not?: Core_Urlparameter_Bool_Exp | null | undefined;
  _or?: Array<Core_Urlparameter_Bool_Exp> | null | undefined;
  core_endpoint?: Core_Endpoint_Bool_Exp | null | undefined;
  data_type?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  key?: String_Comparison_Exp | null | undefined;
  line_number?: Int_Comparison_Exp | null | undefined;
  param_hash?: String_Comparison_Exp | null | undefined;
  param_location?: String_Comparison_Exp | null | undefined;
  source_type?: String_Comparison_Exp | null | undefined;
  value?: String_Comparison_Exp | null | undefined;
  which_endpoint_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_urlparameter" */
export type Core_Urlparameter_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_urlparameter_pkey'
  /** unique or primary key constraint on columns "key", "param_location", "which_endpoint_id" */
  | 'core_urlparameter_which_endpoint_id_param__24efdbf9_uniq';

/** input type for inserting data into table "core_urlparameter" */
export type Core_Urlparameter_Insert_Input = {
  core_endpoint?: Core_Endpoint_Obj_Rel_Insert_Input | null | undefined;
  data_type?: string | null | undefined;
  id?: unknown;
  key?: string | null | undefined;
  line_number?: number | null | undefined;
  param_hash?: string | null | undefined;
  param_location?: string | null | undefined;
  source_type?: string | null | undefined;
  value?: string | null | undefined;
  which_endpoint_id?: unknown;
};

/** on_conflict condition type for table "core_urlparameter" */
export type Core_Urlparameter_On_Conflict = {
  constraint: Core_Urlparameter_Constraint;
  update_columns?: Array<Core_Urlparameter_Update_Column>;
  where?: Core_Urlparameter_Bool_Exp | null | undefined;
};

/** select columns of table "core_urlparameter" */
export type Core_Urlparameter_Select_Column =
  /** column name */
  | 'data_type'
  /** column name */
  | 'id'
  /** column name */
  | 'key'
  /** column name */
  | 'line_number'
  /** column name */
  | 'param_hash'
  /** column name */
  | 'param_location'
  /** column name */
  | 'source_type'
  /** column name */
  | 'value'
  /** column name */
  | 'which_endpoint_id';

/** update columns of table "core_urlparameter" */
export type Core_Urlparameter_Update_Column =
  /** column name */
  | 'data_type'
  /** column name */
  | 'id'
  /** column name */
  | 'key'
  /** column name */
  | 'line_number'
  /** column name */
  | 'param_hash'
  /** column name */
  | 'param_location'
  /** column name */
  | 'source_type'
  /** column name */
  | 'value'
  /** column name */
  | 'which_endpoint_id';

export type Core_Urlresult_Aggregate_Bool_Exp = {
  bool_and?: Core_Urlresult_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Urlresult_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Urlresult_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Urlresult_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Urlresult_Select_Column_Core_Urlresult_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlresult_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Urlresult_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Urlresult_Select_Column_Core_Urlresult_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlresult_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Urlresult_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Urlresult_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlresult_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_urlresult" */
export type Core_Urlresult_Aggregate_Order_By = {
  avg?: Core_Urlresult_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Urlresult_Max_Order_By | null | undefined;
  min?: Core_Urlresult_Min_Order_By | null | undefined;
  stddev?: Core_Urlresult_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Urlresult_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Urlresult_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Urlresult_Sum_Order_By | null | undefined;
  var_pop?: Core_Urlresult_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Urlresult_Var_Samp_Order_By | null | undefined;
  variance?: Core_Urlresult_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_urlresult" */
export type Core_Urlresult_Arr_Rel_Insert_Input = {
  data: Array<Core_Urlresult_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Urlresult_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_urlresult" */
export type Core_Urlresult_Avg_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_urlresult". All fields are combined with a logical 'AND'. */
export type Core_Urlresult_Bool_Exp = {
  _and?: Array<Core_Urlresult_Bool_Exp> | null | undefined;
  _not?: Core_Urlresult_Bool_Exp | null | undefined;
  _or?: Array<Core_Urlresult_Bool_Exp> | null | undefined;
  cleaned_html?: String_Comparison_Exp | null | undefined;
  content_fetch_status?: String_Comparison_Exp | null | undefined;
  content_length?: Int_Comparison_Exp | null | undefined;
  core_analysisfindings?: Core_Analysisfinding_Bool_Exp | null | undefined;
  core_analysisfindings_aggregate?: Core_Analysisfinding_Aggregate_Bool_Exp | null | undefined;
  core_analyzedata?: Core_Analyzedata_Bool_Exp | null | undefined;
  core_analyzedata_aggregate?: Core_Analyzedata_Aggregate_Bool_Exp | null | undefined;
  core_comments?: Core_Comment_Bool_Exp | null | undefined;
  core_comments_aggregate?: Core_Comment_Aggregate_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_urls?: Core_Endpoint_Discovered_By_Urls_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_urls_aggregate?: Core_Endpoint_Discovered_By_Urls_Aggregate_Bool_Exp | null | undefined;
  core_extractedj?: Core_Extractedjs_Bool_Exp | null | undefined;
  core_forms?: Core_Form_Bool_Exp | null | undefined;
  core_forms_aggregate?: Core_Form_Aggregate_Bool_Exp | null | undefined;
  core_iframes?: Core_Iframe_Bool_Exp | null | undefined;
  core_iframes_aggregate?: Core_Iframe_Aggregate_Bool_Exp | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Bool_Exp | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Bool_Exp | null | undefined;
  core_javascriptfile_related_pages?: Core_Javascriptfile_Related_Pages_Bool_Exp | null | undefined;
  core_javascriptfile_related_pages_aggregate?: Core_Javascriptfile_Related_Pages_Aggregate_Bool_Exp | null | undefined;
  core_links?: Core_Link_Bool_Exp | null | undefined;
  core_links_aggregate?: Core_Link_Aggregate_Bool_Exp | null | undefined;
  core_metatags?: Core_Metatag_Bool_Exp | null | undefined;
  core_metatags_aggregate?: Core_Metatag_Aggregate_Bool_Exp | null | undefined;
  core_nucleiscans?: Core_Nucleiscan_Bool_Exp | null | undefined;
  core_nucleiscans_aggregate?: Core_Nucleiscan_Aggregate_Bool_Exp | null | undefined;
  core_overview_url_results?: Core_Overview_Url_Results_Bool_Exp | null | undefined;
  core_overview_url_results_aggregate?: Core_Overview_Url_Results_Aggregate_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_techstacks?: Core_Techstack_Bool_Exp | null | undefined;
  core_techstacks_aggregate?: Core_Techstack_Aggregate_Bool_Exp | null | undefined;
  core_urlresult_discovered_by_scans?: Core_Urlresult_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_urlresult_discovered_by_scans_aggregate?: Core_Urlresult_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  core_urlresult_related_subdomains?: Core_Urlresult_Related_Subdomains_Bool_Exp | null | undefined;
  core_urlresult_related_subdomains_aggregate?: Core_Urlresult_Related_Subdomains_Aggregate_Bool_Exp | null | undefined;
  core_urlscans?: Core_Urlscan_Bool_Exp | null | undefined;
  core_urlscans_aggregate?: Core_Urlscan_Aggregate_Bool_Exp | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Bool_Exp | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  discovery_source?: String_Comparison_Exp | null | undefined;
  dom_snapshot?: String_Comparison_Exp | null | undefined;
  final_url?: String_Comparison_Exp | null | undefined;
  headers?: Jsonb_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  is_external_redirect?: Boolean_Comparison_Exp | null | undefined;
  is_important?: Boolean_Comparison_Exp | null | undefined;
  is_tech_analyzed?: Boolean_Comparison_Exp | null | undefined;
  last_scan_id?: Int_Comparison_Exp | null | undefined;
  last_scan_type?: String_Comparison_Exp | null | undefined;
  method?: String_Comparison_Exp | null | undefined;
  raw_response?: String_Comparison_Exp | null | undefined;
  raw_response_hash?: String_Comparison_Exp | null | undefined;
  status_code?: Int_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  text?: String_Comparison_Exp | null | undefined;
  title?: String_Comparison_Exp | null | undefined;
  url?: String_Comparison_Exp | null | undefined;
  used_flaresolverr?: Boolean_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_urlresult" */
export type Core_Urlresult_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_urlresult_pkey'
  /** unique or primary key constraint on columns "target_id", "url" */
  | 'core_urlresult_target_id_url_98fff105_uniq';

export type Core_Urlresult_Discovered_By_Scans_Aggregate_Bool_Exp = {
  count?: Core_Urlresult_Discovered_By_Scans_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Urlresult_Discovered_By_Scans_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Urlresult_Discovered_By_Scans_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlresult_Discovered_By_Scans_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Aggregate_Order_By = {
  avg?: Core_Urlresult_Discovered_By_Scans_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Urlresult_Discovered_By_Scans_Max_Order_By | null | undefined;
  min?: Core_Urlresult_Discovered_By_Scans_Min_Order_By | null | undefined;
  stddev?: Core_Urlresult_Discovered_By_Scans_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Urlresult_Discovered_By_Scans_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Urlresult_Discovered_By_Scans_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Urlresult_Discovered_By_Scans_Sum_Order_By | null | undefined;
  var_pop?: Core_Urlresult_Discovered_By_Scans_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Urlresult_Discovered_By_Scans_Var_Samp_Order_By | null | undefined;
  variance?: Core_Urlresult_Discovered_By_Scans_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Arr_Rel_Insert_Input = {
  data: Array<Core_Urlresult_Discovered_By_Scans_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Urlresult_Discovered_By_Scans_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Avg_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_urlresult_discovered_by_scans". All fields are combined with a logical 'AND'. */
export type Core_Urlresult_Discovered_By_Scans_Bool_Exp = {
  _and?: Array<Core_Urlresult_Discovered_By_Scans_Bool_Exp> | null | undefined;
  _not?: Core_Urlresult_Discovered_By_Scans_Bool_Exp | null | undefined;
  _or?: Array<Core_Urlresult_Discovered_By_Scans_Bool_Exp> | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  core_urlscan?: Core_Urlscan_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  urlresult_id?: Bigint_Comparison_Exp | null | undefined;
  urlscan_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Constraint =
  /** unique or primary key constraint on columns "urlresult_id", "urlscan_id" */
  | 'core_urlresult_discovere_urlresult_id_urlscan_id_8b9e8455_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_urlresult_discovered_by_scans_pkey';

/** input type for inserting data into table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Insert_Input = {
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  core_urlscan?: Core_Urlscan_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  urlresult_id?: unknown;
  urlscan_id?: unknown;
};

/** order by max() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Max_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Min_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_On_Conflict = {
  constraint: Core_Urlresult_Discovered_By_Scans_Constraint;
  update_columns?: Array<Core_Urlresult_Discovered_By_Scans_Update_Column>;
  where?: Core_Urlresult_Discovered_By_Scans_Bool_Exp | null | undefined;
};

/** select columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'urlresult_id'
  /** column name */
  | 'urlscan_id';

/** order by stddev() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Sum_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** update columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'urlresult_id'
  /** column name */
  | 'urlscan_id';

/** order by var_pop() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_urlresult_discovered_by_scans" */
export type Core_Urlresult_Discovered_By_Scans_Variance_Order_By = {
  id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
  urlscan_id?: Order_By | null | undefined;
};

/** input type for inserting data into table "core_urlresult" */
export type Core_Urlresult_Insert_Input = {
  cleaned_html?: string | null | undefined;
  content_fetch_status?: string | null | undefined;
  content_length?: number | null | undefined;
  core_analysisfindings?: Core_Analysisfinding_Arr_Rel_Insert_Input | null | undefined;
  core_analyzedata?: Core_Analyzedata_Arr_Rel_Insert_Input | null | undefined;
  core_comments?: Core_Comment_Arr_Rel_Insert_Input | null | undefined;
  core_endpoint_discovered_by_urls?: Core_Endpoint_Discovered_By_Urls_Arr_Rel_Insert_Input | null | undefined;
  core_extractedj?: Core_Extractedjs_Obj_Rel_Insert_Input | null | undefined;
  core_forms?: Core_Form_Arr_Rel_Insert_Input | null | undefined;
  core_iframes?: Core_Iframe_Arr_Rel_Insert_Input | null | undefined;
  core_initialaianalyses?: Core_Initialaianalysis_Arr_Rel_Insert_Input | null | undefined;
  core_javascriptfile_related_pages?: Core_Javascriptfile_Related_Pages_Arr_Rel_Insert_Input | null | undefined;
  core_links?: Core_Link_Arr_Rel_Insert_Input | null | undefined;
  core_metatags?: Core_Metatag_Arr_Rel_Insert_Input | null | undefined;
  core_nucleiscans?: Core_Nucleiscan_Arr_Rel_Insert_Input | null | undefined;
  core_overview_url_results?: Core_Overview_Url_Results_Arr_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_techstacks?: Core_Techstack_Arr_Rel_Insert_Input | null | undefined;
  core_urlresult_discovered_by_scans?: Core_Urlresult_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  core_urlresult_related_subdomains?: Core_Urlresult_Related_Subdomains_Arr_Rel_Insert_Input | null | undefined;
  core_urlscans?: Core_Urlscan_Arr_Rel_Insert_Input | null | undefined;
  core_vulnerabilities?: Core_Vulnerability_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  discovery_source?: string | null | undefined;
  dom_snapshot?: string | null | undefined;
  final_url?: string | null | undefined;
  headers?: unknown;
  id?: unknown;
  is_external_redirect?: boolean | null | undefined;
  is_important?: boolean | null | undefined;
  is_tech_analyzed?: boolean | null | undefined;
  last_scan_id?: number | null | undefined;
  last_scan_type?: string | null | undefined;
  method?: string | null | undefined;
  raw_response?: string | null | undefined;
  raw_response_hash?: string | null | undefined;
  status_code?: number | null | undefined;
  target_id?: unknown;
  text?: string | null | undefined;
  title?: string | null | undefined;
  url?: string | null | undefined;
  used_flaresolverr?: boolean | null | undefined;
};

/** order by max() on columns of table "core_urlresult" */
export type Core_Urlresult_Max_Order_By = {
  cleaned_html?: Order_By | null | undefined;
  content_fetch_status?: Order_By | null | undefined;
  content_length?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  discovery_source?: Order_By | null | undefined;
  dom_snapshot?: Order_By | null | undefined;
  final_url?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  raw_response?: Order_By | null | undefined;
  raw_response_hash?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  url?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_urlresult" */
export type Core_Urlresult_Min_Order_By = {
  cleaned_html?: Order_By | null | undefined;
  content_fetch_status?: Order_By | null | undefined;
  content_length?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  discovery_source?: Order_By | null | undefined;
  dom_snapshot?: Order_By | null | undefined;
  final_url?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  raw_response?: Order_By | null | undefined;
  raw_response_hash?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  url?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_urlresult" */
export type Core_Urlresult_Obj_Rel_Insert_Input = {
  data: Core_Urlresult_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Urlresult_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_urlresult" */
export type Core_Urlresult_On_Conflict = {
  constraint: Core_Urlresult_Constraint;
  update_columns?: Array<Core_Urlresult_Update_Column>;
  where?: Core_Urlresult_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_urlresult". */
export type Core_Urlresult_Order_By = {
  cleaned_html?: Order_By | null | undefined;
  content_fetch_status?: Order_By | null | undefined;
  content_length?: Order_By | null | undefined;
  core_analysisfindings_aggregate?: Core_Analysisfinding_Aggregate_Order_By | null | undefined;
  core_analyzedata_aggregate?: Core_Analyzedata_Aggregate_Order_By | null | undefined;
  core_comments_aggregate?: Core_Comment_Aggregate_Order_By | null | undefined;
  core_endpoint_discovered_by_urls_aggregate?: Core_Endpoint_Discovered_By_Urls_Aggregate_Order_By | null | undefined;
  core_extractedj?: Core_Extractedjs_Order_By | null | undefined;
  core_forms_aggregate?: Core_Form_Aggregate_Order_By | null | undefined;
  core_iframes_aggregate?: Core_Iframe_Aggregate_Order_By | null | undefined;
  core_initialaianalyses_aggregate?: Core_Initialaianalysis_Aggregate_Order_By | null | undefined;
  core_javascriptfile_related_pages_aggregate?: Core_Javascriptfile_Related_Pages_Aggregate_Order_By | null | undefined;
  core_links_aggregate?: Core_Link_Aggregate_Order_By | null | undefined;
  core_metatags_aggregate?: Core_Metatag_Aggregate_Order_By | null | undefined;
  core_nucleiscans_aggregate?: Core_Nucleiscan_Aggregate_Order_By | null | undefined;
  core_overview_url_results_aggregate?: Core_Overview_Url_Results_Aggregate_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  core_techstacks_aggregate?: Core_Techstack_Aggregate_Order_By | null | undefined;
  core_urlresult_discovered_by_scans_aggregate?: Core_Urlresult_Discovered_By_Scans_Aggregate_Order_By | null | undefined;
  core_urlresult_related_subdomains_aggregate?: Core_Urlresult_Related_Subdomains_Aggregate_Order_By | null | undefined;
  core_urlscans_aggregate?: Core_Urlscan_Aggregate_Order_By | null | undefined;
  core_vulnerabilities_aggregate?: Core_Vulnerability_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  discovery_source?: Order_By | null | undefined;
  dom_snapshot?: Order_By | null | undefined;
  final_url?: Order_By | null | undefined;
  headers?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  is_external_redirect?: Order_By | null | undefined;
  is_important?: Order_By | null | undefined;
  is_tech_analyzed?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  last_scan_type?: Order_By | null | undefined;
  method?: Order_By | null | undefined;
  raw_response?: Order_By | null | undefined;
  raw_response_hash?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  text?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  url?: Order_By | null | undefined;
  used_flaresolverr?: Order_By | null | undefined;
};

export type Core_Urlresult_Related_Subdomains_Aggregate_Bool_Exp = {
  count?: Core_Urlresult_Related_Subdomains_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Urlresult_Related_Subdomains_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Urlresult_Related_Subdomains_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlresult_Related_Subdomains_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Aggregate_Order_By = {
  avg?: Core_Urlresult_Related_Subdomains_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Urlresult_Related_Subdomains_Max_Order_By | null | undefined;
  min?: Core_Urlresult_Related_Subdomains_Min_Order_By | null | undefined;
  stddev?: Core_Urlresult_Related_Subdomains_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Urlresult_Related_Subdomains_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Urlresult_Related_Subdomains_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Urlresult_Related_Subdomains_Sum_Order_By | null | undefined;
  var_pop?: Core_Urlresult_Related_Subdomains_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Urlresult_Related_Subdomains_Var_Samp_Order_By | null | undefined;
  variance?: Core_Urlresult_Related_Subdomains_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Arr_Rel_Insert_Input = {
  data: Array<Core_Urlresult_Related_Subdomains_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Urlresult_Related_Subdomains_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Avg_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_urlresult_related_subdomains". All fields are combined with a logical 'AND'. */
export type Core_Urlresult_Related_Subdomains_Bool_Exp = {
  _and?: Array<Core_Urlresult_Related_Subdomains_Bool_Exp> | null | undefined;
  _not?: Core_Urlresult_Related_Subdomains_Bool_Exp | null | undefined;
  _or?: Array<Core_Urlresult_Related_Subdomains_Bool_Exp> | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  urlresult_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Constraint =
  /** unique or primary key constraint on columns "urlresult_id", "subdomain_id" */
  | 'core_urlresult_related_s_urlresult_id_subdomain_i_489c3391_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'core_urlresult_related_subdomains_pkey';

/** input type for inserting data into table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Insert_Input = {
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  id?: unknown;
  subdomain_id?: unknown;
  urlresult_id?: unknown;
};

/** order by max() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Max_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Min_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_On_Conflict = {
  constraint: Core_Urlresult_Related_Subdomains_Constraint;
  update_columns?: Array<Core_Urlresult_Related_Subdomains_Update_Column>;
  where?: Core_Urlresult_Related_Subdomains_Bool_Exp | null | undefined;
};

/** select columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Select_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'urlresult_id';

/** order by stddev() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Sum_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** update columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Update_Column =
  /** column name */
  | 'id'
  /** column name */
  | 'subdomain_id'
  /** column name */
  | 'urlresult_id';

/** order by var_pop() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_urlresult_related_subdomains" */
export type Core_Urlresult_Related_Subdomains_Variance_Order_By = {
  id?: Order_By | null | undefined;
  subdomain_id?: Order_By | null | undefined;
  urlresult_id?: Order_By | null | undefined;
};

/** select columns of table "core_urlresult" */
export type Core_Urlresult_Select_Column =
  /** column name */
  | 'cleaned_html'
  /** column name */
  | 'content_fetch_status'
  /** column name */
  | 'content_length'
  /** column name */
  | 'created_at'
  /** column name */
  | 'discovery_source'
  /** column name */
  | 'dom_snapshot'
  /** column name */
  | 'final_url'
  /** column name */
  | 'headers'
  /** column name */
  | 'id'
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'method'
  /** column name */
  | 'raw_response'
  /** column name */
  | 'raw_response_hash'
  /** column name */
  | 'status_code'
  /** column name */
  | 'target_id'
  /** column name */
  | 'text'
  /** column name */
  | 'title'
  /** column name */
  | 'url'
  /** column name */
  | 'used_flaresolverr';

/** select "core_urlresult_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_urlresult" */
export type Core_Urlresult_Select_Column_Core_Urlresult_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'used_flaresolverr';

/** select "core_urlresult_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_urlresult" */
export type Core_Urlresult_Select_Column_Core_Urlresult_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'used_flaresolverr';

/** order by stddev() on columns of table "core_urlresult" */
export type Core_Urlresult_Stddev_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_urlresult" */
export type Core_Urlresult_Stddev_Pop_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_urlresult" */
export type Core_Urlresult_Stddev_Samp_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_urlresult" */
export type Core_Urlresult_Sum_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** update columns of table "core_urlresult" */
export type Core_Urlresult_Update_Column =
  /** column name */
  | 'cleaned_html'
  /** column name */
  | 'content_fetch_status'
  /** column name */
  | 'content_length'
  /** column name */
  | 'created_at'
  /** column name */
  | 'discovery_source'
  /** column name */
  | 'dom_snapshot'
  /** column name */
  | 'final_url'
  /** column name */
  | 'headers'
  /** column name */
  | 'id'
  /** column name */
  | 'is_external_redirect'
  /** column name */
  | 'is_important'
  /** column name */
  | 'is_tech_analyzed'
  /** column name */
  | 'last_scan_id'
  /** column name */
  | 'last_scan_type'
  /** column name */
  | 'method'
  /** column name */
  | 'raw_response'
  /** column name */
  | 'raw_response_hash'
  /** column name */
  | 'status_code'
  /** column name */
  | 'target_id'
  /** column name */
  | 'text'
  /** column name */
  | 'title'
  /** column name */
  | 'url'
  /** column name */
  | 'used_flaresolverr';

/** order by var_pop() on columns of table "core_urlresult" */
export type Core_Urlresult_Var_Pop_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_urlresult" */
export type Core_Urlresult_Var_Samp_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_urlresult" */
export type Core_Urlresult_Variance_Order_By = {
  content_length?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  last_scan_id?: Order_By | null | undefined;
  status_code?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
};

export type Core_Urlscan_Aggregate_Bool_Exp = {
  count?: Core_Urlscan_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Urlscan_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Urlscan_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Urlscan_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_urlscan" */
export type Core_Urlscan_Aggregate_Order_By = {
  avg?: Core_Urlscan_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Urlscan_Max_Order_By | null | undefined;
  min?: Core_Urlscan_Min_Order_By | null | undefined;
  stddev?: Core_Urlscan_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Urlscan_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Urlscan_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Urlscan_Sum_Order_By | null | undefined;
  var_pop?: Core_Urlscan_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Urlscan_Var_Samp_Order_By | null | undefined;
  variance?: Core_Urlscan_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_urlscan" */
export type Core_Urlscan_Arr_Rel_Insert_Input = {
  data: Array<Core_Urlscan_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Urlscan_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_urlscan" */
export type Core_Urlscan_Avg_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_urlscan". All fields are combined with a logical 'AND'. */
export type Core_Urlscan_Bool_Exp = {
  _and?: Array<Core_Urlscan_Bool_Exp> | null | undefined;
  _not?: Core_Urlscan_Bool_Exp | null | undefined;
  _or?: Array<Core_Urlscan_Bool_Exp> | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  core_endpoint_discovered_by_scans?: Core_Endpoint_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_endpoint_discovered_by_scans_aggregate?: Core_Endpoint_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  core_urlresult_discovered_by_scans?: Core_Urlresult_Discovered_By_Scans_Bool_Exp | null | undefined;
  core_urlresult_discovered_by_scans_aggregate?: Core_Urlresult_Discovered_By_Scans_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error_message?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  target_subdomain_id?: Bigint_Comparison_Exp | null | undefined;
  target_url_id?: Bigint_Comparison_Exp | null | undefined;
  tool?: String_Comparison_Exp | null | undefined;
  urls_found_count?: Int_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_urlscan" */
export type Core_Urlscan_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_urlscan_pkey';

/** input type for inserting data into table "core_urlscan" */
export type Core_Urlscan_Insert_Input = {
  completed_at?: unknown;
  core_endpoint_discovered_by_scans?: Core_Endpoint_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult_discovered_by_scans?: Core_Urlresult_Discovered_By_Scans_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  error_message?: string | null | undefined;
  id?: unknown;
  started_at?: unknown;
  status?: string | null | undefined;
  target_subdomain_id?: unknown;
  target_url_id?: unknown;
  tool?: string | null | undefined;
  urls_found_count?: number | null | undefined;
};

/** order by max() on columns of table "core_urlscan" */
export type Core_Urlscan_Max_Order_By = {
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  tool?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_urlscan" */
export type Core_Urlscan_Min_Order_By = {
  completed_at?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  error_message?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  tool?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_urlscan" */
export type Core_Urlscan_Obj_Rel_Insert_Input = {
  data: Core_Urlscan_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Urlscan_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_urlscan" */
export type Core_Urlscan_On_Conflict = {
  constraint: Core_Urlscan_Constraint;
  update_columns?: Array<Core_Urlscan_Update_Column>;
  where?: Core_Urlscan_Bool_Exp | null | undefined;
};

/** select columns of table "core_urlscan" */
export type Core_Urlscan_Select_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'target_subdomain_id'
  /** column name */
  | 'target_url_id'
  /** column name */
  | 'tool'
  /** column name */
  | 'urls_found_count';

/** order by stddev() on columns of table "core_urlscan" */
export type Core_Urlscan_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_urlscan" */
export type Core_Urlscan_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_urlscan" */
export type Core_Urlscan_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_urlscan" */
export type Core_Urlscan_Sum_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** update columns of table "core_urlscan" */
export type Core_Urlscan_Update_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error_message'
  /** column name */
  | 'id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'target_subdomain_id'
  /** column name */
  | 'target_url_id'
  /** column name */
  | 'tool'
  /** column name */
  | 'urls_found_count';

/** order by var_pop() on columns of table "core_urlscan" */
export type Core_Urlscan_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_urlscan" */
export type Core_Urlscan_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_urlscan" */
export type Core_Urlscan_Variance_Order_By = {
  id?: Order_By | null | undefined;
  target_subdomain_id?: Order_By | null | undefined;
  target_url_id?: Order_By | null | undefined;
  urls_found_count?: Order_By | null | undefined;
};

export type Core_Verification_Aggregate_Bool_Exp = {
  bool_and?: Core_Verification_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Core_Verification_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Core_Verification_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Verification_Aggregate_Bool_Exp_Bool_And = {
  arguments: Core_Verification_Select_Column_Core_Verification_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Verification_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Verification_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Core_Verification_Select_Column_Core_Verification_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Core_Verification_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Core_Verification_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Verification_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Verification_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_verification" */
export type Core_Verification_Aggregate_Order_By = {
  avg?: Core_Verification_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Verification_Max_Order_By | null | undefined;
  min?: Core_Verification_Min_Order_By | null | undefined;
  stddev?: Core_Verification_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Verification_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Verification_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Verification_Sum_Order_By | null | undefined;
  var_pop?: Core_Verification_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Verification_Var_Samp_Order_By | null | undefined;
  variance?: Core_Verification_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_verification" */
export type Core_Verification_Arr_Rel_Insert_Input = {
  data: Array<Core_Verification_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Verification_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_verification" */
export type Core_Verification_Avg_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_verification". All fields are combined with a logical 'AND'. */
export type Core_Verification_Bool_Exp = {
  _and?: Array<Core_Verification_Bool_Exp> | null | undefined;
  _not?: Core_Verification_Bool_Exp | null | undefined;
  _or?: Array<Core_Verification_Bool_Exp> | null | undefined;
  ai_response?: Jsonb_Comparison_Exp | null | undefined;
  attack_vector_id?: Bigint_Comparison_Exp | null | undefined;
  auto_create_vulnerability?: Boolean_Comparison_Exp | null | undefined;
  confidence?: Int_Comparison_Exp | null | undefined;
  confidence_threshold?: Smallint_Comparison_Exp | null | undefined;
  core_attackvector?: Core_Attackvector_Bool_Exp | null | undefined;
  core_vulnerability?: Core_Vulnerability_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  evidence?: String_Comparison_Exp | null | undefined;
  execution_output?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  match_type?: String_Comparison_Exp | null | undefined;
  observation_prompt?: String_Comparison_Exp | null | undefined;
  pattern?: String_Comparison_Exp | null | undefined;
  reason?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  verdict?: String_Comparison_Exp | null | undefined;
  vulnerability_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_verification" */
export type Core_Verification_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'core_verification_pkey';

/** input type for inserting data into table "core_verification" */
export type Core_Verification_Insert_Input = {
  ai_response?: unknown;
  attack_vector_id?: unknown;
  auto_create_vulnerability?: boolean | null | undefined;
  confidence?: number | null | undefined;
  confidence_threshold?: unknown;
  core_attackvector?: Core_Attackvector_Obj_Rel_Insert_Input | null | undefined;
  core_vulnerability?: Core_Vulnerability_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  evidence?: string | null | undefined;
  execution_output?: string | null | undefined;
  id?: unknown;
  match_type?: string | null | undefined;
  observation_prompt?: string | null | undefined;
  pattern?: string | null | undefined;
  reason?: string | null | undefined;
  updated_at?: unknown;
  verdict?: string | null | undefined;
  vulnerability_id?: unknown;
};

/** order by max() on columns of table "core_verification" */
export type Core_Verification_Max_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  evidence?: Order_By | null | undefined;
  execution_output?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  match_type?: Order_By | null | undefined;
  observation_prompt?: Order_By | null | undefined;
  pattern?: Order_By | null | undefined;
  reason?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  verdict?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_verification" */
export type Core_Verification_Min_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  evidence?: Order_By | null | undefined;
  execution_output?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  match_type?: Order_By | null | undefined;
  observation_prompt?: Order_By | null | undefined;
  pattern?: Order_By | null | undefined;
  reason?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  verdict?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "core_verification" */
export type Core_Verification_On_Conflict = {
  constraint: Core_Verification_Constraint;
  update_columns?: Array<Core_Verification_Update_Column>;
  where?: Core_Verification_Bool_Exp | null | undefined;
};

/** select columns of table "core_verification" */
export type Core_Verification_Select_Column =
  /** column name */
  | 'ai_response'
  /** column name */
  | 'attack_vector_id'
  /** column name */
  | 'auto_create_vulnerability'
  /** column name */
  | 'confidence'
  /** column name */
  | 'confidence_threshold'
  /** column name */
  | 'created_at'
  /** column name */
  | 'evidence'
  /** column name */
  | 'execution_output'
  /** column name */
  | 'id'
  /** column name */
  | 'match_type'
  /** column name */
  | 'observation_prompt'
  /** column name */
  | 'pattern'
  /** column name */
  | 'reason'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'verdict'
  /** column name */
  | 'vulnerability_id';

/** select "core_verification_aggregate_bool_exp_bool_and_arguments_columns" columns of table "core_verification" */
export type Core_Verification_Select_Column_Core_Verification_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'auto_create_vulnerability';

/** select "core_verification_aggregate_bool_exp_bool_or_arguments_columns" columns of table "core_verification" */
export type Core_Verification_Select_Column_Core_Verification_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'auto_create_vulnerability';

/** order by stddev() on columns of table "core_verification" */
export type Core_Verification_Stddev_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_verification" */
export type Core_Verification_Stddev_Pop_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_verification" */
export type Core_Verification_Stddev_Samp_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_verification" */
export type Core_Verification_Sum_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** update columns of table "core_verification" */
export type Core_Verification_Update_Column =
  /** column name */
  | 'ai_response'
  /** column name */
  | 'attack_vector_id'
  /** column name */
  | 'auto_create_vulnerability'
  /** column name */
  | 'confidence'
  /** column name */
  | 'confidence_threshold'
  /** column name */
  | 'created_at'
  /** column name */
  | 'evidence'
  /** column name */
  | 'execution_output'
  /** column name */
  | 'id'
  /** column name */
  | 'match_type'
  /** column name */
  | 'observation_prompt'
  /** column name */
  | 'pattern'
  /** column name */
  | 'reason'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'verdict'
  /** column name */
  | 'vulnerability_id';

/** order by var_pop() on columns of table "core_verification" */
export type Core_Verification_Var_Pop_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_verification" */
export type Core_Verification_Var_Samp_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_verification" */
export type Core_Verification_Variance_Order_By = {
  attack_vector_id?: Order_By | null | undefined;
  confidence?: Order_By | null | undefined;
  confidence_threshold?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  vulnerability_id?: Order_By | null | undefined;
};

export type Core_Vulnerability_Aggregate_Bool_Exp = {
  count?: Core_Vulnerability_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Core_Vulnerability_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Core_Vulnerability_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Core_Vulnerability_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "core_vulnerability" */
export type Core_Vulnerability_Aggregate_Order_By = {
  avg?: Core_Vulnerability_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Core_Vulnerability_Max_Order_By | null | undefined;
  min?: Core_Vulnerability_Min_Order_By | null | undefined;
  stddev?: Core_Vulnerability_Stddev_Order_By | null | undefined;
  stddev_pop?: Core_Vulnerability_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Core_Vulnerability_Stddev_Samp_Order_By | null | undefined;
  sum?: Core_Vulnerability_Sum_Order_By | null | undefined;
  var_pop?: Core_Vulnerability_Var_Pop_Order_By | null | undefined;
  var_samp?: Core_Vulnerability_Var_Samp_Order_By | null | undefined;
  variance?: Core_Vulnerability_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "core_vulnerability" */
export type Core_Vulnerability_Arr_Rel_Insert_Input = {
  data: Array<Core_Vulnerability_Insert_Input>;
  /** upsert condition */
  on_conflict?: Core_Vulnerability_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Avg_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "core_vulnerability". All fields are combined with a logical 'AND'. */
export type Core_Vulnerability_Bool_Exp = {
  _and?: Array<Core_Vulnerability_Bool_Exp> | null | undefined;
  _not?: Core_Vulnerability_Bool_Exp | null | undefined;
  _or?: Array<Core_Vulnerability_Bool_Exp> | null | undefined;
  action_id?: Bigint_Comparison_Exp | null | undefined;
  core_attackvector?: Core_Attackvector_Bool_Exp | null | undefined;
  core_cveintelligence?: Core_Cveintelligence_Bool_Exp | null | undefined;
  core_ip?: Core_Ip_Bool_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  core_pocrecords?: Core_Pocrecord_Bool_Exp | null | undefined;
  core_pocrecords_aggregate?: Core_Pocrecord_Aggregate_Bool_Exp | null | undefined;
  core_subdomain?: Core_Subdomain_Bool_Exp | null | undefined;
  core_target?: Core_Target_Bool_Exp | null | undefined;
  core_urlresult?: Core_Urlresult_Bool_Exp | null | undefined;
  core_verifications?: Core_Verification_Bool_Exp | null | undefined;
  core_verifications_aggregate?: Core_Verification_Aggregate_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  cve_intelligence_id?: Bigint_Comparison_Exp | null | undefined;
  description?: String_Comparison_Exp | null | undefined;
  enrichment_attempted_at?: Timestamptz_Comparison_Exp | null | undefined;
  enrichment_status?: String_Comparison_Exp | null | undefined;
  extracted_results?: Jsonb_Comparison_Exp | null | undefined;
  fingerprint?: String_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  ip_asset_id?: Bigint_Comparison_Exp | null | undefined;
  last_seen?: Timestamptz_Comparison_Exp | null | undefined;
  matched_at?: String_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  remediation?: String_Comparison_Exp | null | undefined;
  request_raw?: String_Comparison_Exp | null | undefined;
  response_raw?: String_Comparison_Exp | null | undefined;
  severity?: String_Comparison_Exp | null | undefined;
  source_attack_vector_id?: Bigint_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  subdomain_asset_id?: Bigint_Comparison_Exp | null | undefined;
  target_id?: Bigint_Comparison_Exp | null | undefined;
  template_id?: String_Comparison_Exp | null | undefined;
  tool_source?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  url_asset_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "core_vulnerability" */
export type Core_Vulnerability_Constraint =
  /** unique or primary key constraint on columns "fingerprint" */
  | 'core_vulnerability_fingerprint_key'
  /** unique or primary key constraint on columns "id" */
  | 'core_vulnerability_pkey';

/** input type for inserting data into table "core_vulnerability" */
export type Core_Vulnerability_Insert_Input = {
  action_id?: unknown;
  core_attackvector?: Core_Attackvector_Obj_Rel_Insert_Input | null | undefined;
  core_cveintelligence?: Core_Cveintelligence_Obj_Rel_Insert_Input | null | undefined;
  core_ip?: Core_Ip_Obj_Rel_Insert_Input | null | undefined;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  core_pocrecords?: Core_Pocrecord_Arr_Rel_Insert_Input | null | undefined;
  core_subdomain?: Core_Subdomain_Obj_Rel_Insert_Input | null | undefined;
  core_target?: Core_Target_Obj_Rel_Insert_Input | null | undefined;
  core_urlresult?: Core_Urlresult_Obj_Rel_Insert_Input | null | undefined;
  core_verifications?: Core_Verification_Arr_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  cve_intelligence_id?: unknown;
  description?: string | null | undefined;
  enrichment_attempted_at?: unknown;
  enrichment_status?: string | null | undefined;
  extracted_results?: unknown;
  fingerprint?: string | null | undefined;
  id?: unknown;
  ip_asset_id?: unknown;
  last_seen?: unknown;
  matched_at?: string | null | undefined;
  name?: string | null | undefined;
  overview_id?: unknown;
  remediation?: string | null | undefined;
  request_raw?: string | null | undefined;
  response_raw?: string | null | undefined;
  severity?: string | null | undefined;
  source_attack_vector_id?: unknown;
  status?: string | null | undefined;
  subdomain_asset_id?: unknown;
  target_id?: unknown;
  template_id?: string | null | undefined;
  tool_source?: string | null | undefined;
  updated_at?: unknown;
  url_asset_id?: unknown;
};

/** order by max() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Max_Order_By = {
  action_id?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  enrichment_attempted_at?: Order_By | null | undefined;
  enrichment_status?: Order_By | null | undefined;
  fingerprint?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  matched_at?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  remediation?: Order_By | null | undefined;
  request_raw?: Order_By | null | undefined;
  response_raw?: Order_By | null | undefined;
  severity?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  template_id?: Order_By | null | undefined;
  tool_source?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Min_Order_By = {
  action_id?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  enrichment_attempted_at?: Order_By | null | undefined;
  enrichment_status?: Order_By | null | undefined;
  fingerprint?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  matched_at?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  remediation?: Order_By | null | undefined;
  request_raw?: Order_By | null | undefined;
  response_raw?: Order_By | null | undefined;
  severity?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  template_id?: Order_By | null | undefined;
  tool_source?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "core_vulnerability" */
export type Core_Vulnerability_Obj_Rel_Insert_Input = {
  data: Core_Vulnerability_Insert_Input;
  /** upsert condition */
  on_conflict?: Core_Vulnerability_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "core_vulnerability" */
export type Core_Vulnerability_On_Conflict = {
  constraint: Core_Vulnerability_Constraint;
  update_columns?: Array<Core_Vulnerability_Update_Column>;
  where?: Core_Vulnerability_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "core_vulnerability". */
export type Core_Vulnerability_Order_By = {
  action_id?: Order_By | null | undefined;
  core_attackvector?: Core_Attackvector_Order_By | null | undefined;
  core_cveintelligence?: Core_Cveintelligence_Order_By | null | undefined;
  core_ip?: Core_Ip_Order_By | null | undefined;
  core_overview?: Core_Overview_Order_By | null | undefined;
  core_pocrecords_aggregate?: Core_Pocrecord_Aggregate_Order_By | null | undefined;
  core_subdomain?: Core_Subdomain_Order_By | null | undefined;
  core_target?: Core_Target_Order_By | null | undefined;
  core_urlresult?: Core_Urlresult_Order_By | null | undefined;
  core_verifications_aggregate?: Core_Verification_Aggregate_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  description?: Order_By | null | undefined;
  enrichment_attempted_at?: Order_By | null | undefined;
  enrichment_status?: Order_By | null | undefined;
  extracted_results?: Order_By | null | undefined;
  fingerprint?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  last_seen?: Order_By | null | undefined;
  matched_at?: Order_By | null | undefined;
  name?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  remediation?: Order_By | null | undefined;
  request_raw?: Order_By | null | undefined;
  response_raw?: Order_By | null | undefined;
  severity?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  template_id?: Order_By | null | undefined;
  tool_source?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** select columns of table "core_vulnerability" */
export type Core_Vulnerability_Select_Column =
  /** column name */
  | 'action_id'
  /** column name */
  | 'created_at'
  /** column name */
  | 'cve_intelligence_id'
  /** column name */
  | 'description'
  /** column name */
  | 'enrichment_attempted_at'
  /** column name */
  | 'enrichment_status'
  /** column name */
  | 'extracted_results'
  /** column name */
  | 'fingerprint'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_asset_id'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'matched_at'
  /** column name */
  | 'name'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'remediation'
  /** column name */
  | 'request_raw'
  /** column name */
  | 'response_raw'
  /** column name */
  | 'severity'
  /** column name */
  | 'source_attack_vector_id'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_asset_id'
  /** column name */
  | 'target_id'
  /** column name */
  | 'template_id'
  /** column name */
  | 'tool_source'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'url_asset_id';

/** input type for updating data in table "core_vulnerability" */
export type Core_Vulnerability_Set_Input = {
  action_id?: unknown;
  created_at?: unknown;
  cve_intelligence_id?: unknown;
  description?: string | null | undefined;
  enrichment_attempted_at?: unknown;
  enrichment_status?: string | null | undefined;
  extracted_results?: unknown;
  fingerprint?: string | null | undefined;
  id?: unknown;
  ip_asset_id?: unknown;
  last_seen?: unknown;
  matched_at?: string | null | undefined;
  name?: string | null | undefined;
  overview_id?: unknown;
  remediation?: string | null | undefined;
  request_raw?: string | null | undefined;
  response_raw?: string | null | undefined;
  severity?: string | null | undefined;
  source_attack_vector_id?: unknown;
  status?: string | null | undefined;
  subdomain_asset_id?: unknown;
  target_id?: unknown;
  template_id?: string | null | undefined;
  tool_source?: string | null | undefined;
  updated_at?: unknown;
  url_asset_id?: unknown;
};

/** order by stddev() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Stddev_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Stddev_Pop_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Stddev_Samp_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Sum_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** update columns of table "core_vulnerability" */
export type Core_Vulnerability_Update_Column =
  /** column name */
  | 'action_id'
  /** column name */
  | 'created_at'
  /** column name */
  | 'cve_intelligence_id'
  /** column name */
  | 'description'
  /** column name */
  | 'enrichment_attempted_at'
  /** column name */
  | 'enrichment_status'
  /** column name */
  | 'extracted_results'
  /** column name */
  | 'fingerprint'
  /** column name */
  | 'id'
  /** column name */
  | 'ip_asset_id'
  /** column name */
  | 'last_seen'
  /** column name */
  | 'matched_at'
  /** column name */
  | 'name'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'remediation'
  /** column name */
  | 'request_raw'
  /** column name */
  | 'response_raw'
  /** column name */
  | 'severity'
  /** column name */
  | 'source_attack_vector_id'
  /** column name */
  | 'status'
  /** column name */
  | 'subdomain_asset_id'
  /** column name */
  | 'target_id'
  /** column name */
  | 'template_id'
  /** column name */
  | 'tool_source'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'url_asset_id';

/** order by var_pop() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Var_Pop_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Var_Samp_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "core_vulnerability" */
export type Core_Vulnerability_Variance_Order_By = {
  action_id?: Order_By | null | undefined;
  cve_intelligence_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  ip_asset_id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  source_attack_vector_id?: Order_By | null | undefined;
  subdomain_asset_id?: Order_By | null | undefined;
  target_id?: Order_By | null | undefined;
  url_asset_id?: Order_By | null | undefined;
};

export type Django_Admin_Log_Aggregate_Bool_Exp = {
  count?: Django_Admin_Log_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Django_Admin_Log_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Django_Admin_Log_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Django_Admin_Log_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "django_admin_log" */
export type Django_Admin_Log_Aggregate_Order_By = {
  avg?: Django_Admin_Log_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Django_Admin_Log_Max_Order_By | null | undefined;
  min?: Django_Admin_Log_Min_Order_By | null | undefined;
  stddev?: Django_Admin_Log_Stddev_Order_By | null | undefined;
  stddev_pop?: Django_Admin_Log_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Django_Admin_Log_Stddev_Samp_Order_By | null | undefined;
  sum?: Django_Admin_Log_Sum_Order_By | null | undefined;
  var_pop?: Django_Admin_Log_Var_Pop_Order_By | null | undefined;
  var_samp?: Django_Admin_Log_Var_Samp_Order_By | null | undefined;
  variance?: Django_Admin_Log_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "django_admin_log" */
export type Django_Admin_Log_Arr_Rel_Insert_Input = {
  data: Array<Django_Admin_Log_Insert_Input>;
  /** upsert condition */
  on_conflict?: Django_Admin_Log_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "django_admin_log" */
export type Django_Admin_Log_Avg_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "django_admin_log". All fields are combined with a logical 'AND'. */
export type Django_Admin_Log_Bool_Exp = {
  _and?: Array<Django_Admin_Log_Bool_Exp> | null | undefined;
  _not?: Django_Admin_Log_Bool_Exp | null | undefined;
  _or?: Array<Django_Admin_Log_Bool_Exp> | null | undefined;
  action_flag?: Smallint_Comparison_Exp | null | undefined;
  action_time?: Timestamptz_Comparison_Exp | null | undefined;
  auth_user?: Auth_User_Bool_Exp | null | undefined;
  change_message?: String_Comparison_Exp | null | undefined;
  content_type_id?: Int_Comparison_Exp | null | undefined;
  django_content_type?: Django_Content_Type_Bool_Exp | null | undefined;
  id?: Int_Comparison_Exp | null | undefined;
  object_id?: String_Comparison_Exp | null | undefined;
  object_repr?: String_Comparison_Exp | null | undefined;
  user_id?: Int_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "django_admin_log" */
export type Django_Admin_Log_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'django_admin_log_pkey';

/** input type for inserting data into table "django_admin_log" */
export type Django_Admin_Log_Insert_Input = {
  action_flag?: unknown;
  action_time?: unknown;
  auth_user?: Auth_User_Obj_Rel_Insert_Input | null | undefined;
  change_message?: string | null | undefined;
  content_type_id?: number | null | undefined;
  django_content_type?: Django_Content_Type_Obj_Rel_Insert_Input | null | undefined;
  id?: number | null | undefined;
  object_id?: string | null | undefined;
  object_repr?: string | null | undefined;
  user_id?: number | null | undefined;
};

/** order by max() on columns of table "django_admin_log" */
export type Django_Admin_Log_Max_Order_By = {
  action_flag?: Order_By | null | undefined;
  action_time?: Order_By | null | undefined;
  change_message?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  object_id?: Order_By | null | undefined;
  object_repr?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by min() on columns of table "django_admin_log" */
export type Django_Admin_Log_Min_Order_By = {
  action_flag?: Order_By | null | undefined;
  action_time?: Order_By | null | undefined;
  change_message?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  object_id?: Order_By | null | undefined;
  object_repr?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** on_conflict condition type for table "django_admin_log" */
export type Django_Admin_Log_On_Conflict = {
  constraint: Django_Admin_Log_Constraint;
  update_columns?: Array<Django_Admin_Log_Update_Column>;
  where?: Django_Admin_Log_Bool_Exp | null | undefined;
};

/** select columns of table "django_admin_log" */
export type Django_Admin_Log_Select_Column =
  /** column name */
  | 'action_flag'
  /** column name */
  | 'action_time'
  /** column name */
  | 'change_message'
  /** column name */
  | 'content_type_id'
  /** column name */
  | 'id'
  /** column name */
  | 'object_id'
  /** column name */
  | 'object_repr'
  /** column name */
  | 'user_id';

/** order by stddev() on columns of table "django_admin_log" */
export type Django_Admin_Log_Stddev_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "django_admin_log" */
export type Django_Admin_Log_Stddev_Pop_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "django_admin_log" */
export type Django_Admin_Log_Stddev_Samp_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "django_admin_log" */
export type Django_Admin_Log_Sum_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** update columns of table "django_admin_log" */
export type Django_Admin_Log_Update_Column =
  /** column name */
  | 'action_flag'
  /** column name */
  | 'action_time'
  /** column name */
  | 'change_message'
  /** column name */
  | 'content_type_id'
  /** column name */
  | 'id'
  /** column name */
  | 'object_id'
  /** column name */
  | 'object_repr'
  /** column name */
  | 'user_id';

/** order by var_pop() on columns of table "django_admin_log" */
export type Django_Admin_Log_Var_Pop_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "django_admin_log" */
export type Django_Admin_Log_Var_Samp_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "django_admin_log" */
export type Django_Admin_Log_Variance_Order_By = {
  action_flag?: Order_By | null | undefined;
  content_type_id?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  user_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "django_content_type". All fields are combined with a logical 'AND'. */
export type Django_Content_Type_Bool_Exp = {
  _and?: Array<Django_Content_Type_Bool_Exp> | null | undefined;
  _not?: Django_Content_Type_Bool_Exp | null | undefined;
  _or?: Array<Django_Content_Type_Bool_Exp> | null | undefined;
  app_label?: String_Comparison_Exp | null | undefined;
  auth_permissions?: Auth_Permission_Bool_Exp | null | undefined;
  auth_permissions_aggregate?: Auth_Permission_Aggregate_Bool_Exp | null | undefined;
  django_admin_logs?: Django_Admin_Log_Bool_Exp | null | undefined;
  django_admin_logs_aggregate?: Django_Admin_Log_Aggregate_Bool_Exp | null | undefined;
  id?: Int_Comparison_Exp | null | undefined;
  model?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "django_content_type" */
export type Django_Content_Type_Constraint =
  /** unique or primary key constraint on columns "app_label", "model" */
  | 'django_content_type_app_label_model_76bd3d3b_uniq'
  /** unique or primary key constraint on columns "id" */
  | 'django_content_type_pkey';

/** input type for inserting data into table "django_content_type" */
export type Django_Content_Type_Insert_Input = {
  app_label?: string | null | undefined;
  auth_permissions?: Auth_Permission_Arr_Rel_Insert_Input | null | undefined;
  django_admin_logs?: Django_Admin_Log_Arr_Rel_Insert_Input | null | undefined;
  id?: number | null | undefined;
  model?: string | null | undefined;
};

/** input type for inserting object relation for remote table "django_content_type" */
export type Django_Content_Type_Obj_Rel_Insert_Input = {
  data: Django_Content_Type_Insert_Input;
  /** upsert condition */
  on_conflict?: Django_Content_Type_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "django_content_type" */
export type Django_Content_Type_On_Conflict = {
  constraint: Django_Content_Type_Constraint;
  update_columns?: Array<Django_Content_Type_Update_Column>;
  where?: Django_Content_Type_Bool_Exp | null | undefined;
};

/** update columns of table "django_content_type" */
export type Django_Content_Type_Update_Column =
  /** column name */
  | 'app_label'
  /** column name */
  | 'id'
  /** column name */
  | 'model';

export type Execution_Artifact_Aggregate_Bool_Exp = {
  count?: Execution_Artifact_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Execution_Artifact_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Execution_Artifact_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Execution_Artifact_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "execution_artifact" */
export type Execution_Artifact_Arr_Rel_Insert_Input = {
  data: Array<Execution_Artifact_Insert_Input>;
  /** upsert condition */
  on_conflict?: Execution_Artifact_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "execution_artifact". All fields are combined with a logical 'AND'. */
export type Execution_Artifact_Bool_Exp = {
  _and?: Array<Execution_Artifact_Bool_Exp> | null | undefined;
  _not?: Execution_Artifact_Bool_Exp | null | undefined;
  _or?: Array<Execution_Artifact_Bool_Exp> | null | undefined;
  artifact_type?: String_Comparison_Exp | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  content_blob_id?: Bigint_Comparison_Exp | null | undefined;
  core_content_blob?: Core_Content_Blob_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  data?: Jsonb_Comparison_Exp | null | undefined;
  execution_graph?: Execution_Graph_Bool_Exp | null | undefined;
  execution_node?: Execution_Node_Bool_Exp | null | undefined;
  graph_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  metadata?: Jsonb_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  node_id?: Bigint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "execution_artifact" */
export type Execution_Artifact_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'execution_artifact_pkey';

/** input type for inserting data into table "execution_artifact" */
export type Execution_Artifact_Insert_Input = {
  artifact_type?: string | null | undefined;
  content?: string | null | undefined;
  content_blob_id?: unknown;
  core_content_blob?: Core_Content_Blob_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  data?: unknown;
  execution_graph?: Execution_Graph_Obj_Rel_Insert_Input | null | undefined;
  execution_node?: Execution_Node_Obj_Rel_Insert_Input | null | undefined;
  graph_id?: unknown;
  id?: unknown;
  metadata?: unknown;
  name?: string | null | undefined;
  node_id?: unknown;
};

/** on_conflict condition type for table "execution_artifact" */
export type Execution_Artifact_On_Conflict = {
  constraint: Execution_Artifact_Constraint;
  update_columns?: Array<Execution_Artifact_Update_Column>;
  where?: Execution_Artifact_Bool_Exp | null | undefined;
};

/** select columns of table "execution_artifact" */
export type Execution_Artifact_Select_Column =
  /** column name */
  | 'artifact_type'
  /** column name */
  | 'content'
  /** column name */
  | 'content_blob_id'
  /** column name */
  | 'created_at'
  /** column name */
  | 'data'
  /** column name */
  | 'graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'metadata'
  /** column name */
  | 'name'
  /** column name */
  | 'node_id';

/** update columns of table "execution_artifact" */
export type Execution_Artifact_Update_Column =
  /** column name */
  | 'artifact_type'
  /** column name */
  | 'content'
  /** column name */
  | 'content_blob_id'
  /** column name */
  | 'created_at'
  /** column name */
  | 'data'
  /** column name */
  | 'graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'metadata'
  /** column name */
  | 'name'
  /** column name */
  | 'node_id';

export type Execution_Event_Aggregate_Bool_Exp = {
  count?: Execution_Event_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Execution_Event_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Execution_Event_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Execution_Event_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "execution_event" */
export type Execution_Event_Arr_Rel_Insert_Input = {
  data: Array<Execution_Event_Insert_Input>;
  /** upsert condition */
  on_conflict?: Execution_Event_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "execution_event". All fields are combined with a logical 'AND'. */
export type Execution_Event_Bool_Exp = {
  _and?: Array<Execution_Event_Bool_Exp> | null | undefined;
  _not?: Execution_Event_Bool_Exp | null | undefined;
  _or?: Array<Execution_Event_Bool_Exp> | null | undefined;
  content?: String_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  event_type?: String_Comparison_Exp | null | undefined;
  execution_graph?: Execution_Graph_Bool_Exp | null | undefined;
  execution_node?: Execution_Node_Bool_Exp | null | undefined;
  graph_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  node_id?: Bigint_Comparison_Exp | null | undefined;
  payload?: Jsonb_Comparison_Exp | null | undefined;
  sequence?: Bigint_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "execution_event" */
export type Execution_Event_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'execution_event_pkey'
  /** unique or primary key constraint on columns "graph_id", "sequence" */
  | 'uniq_exec_event_graph_seq';

/** input type for inserting data into table "execution_event" */
export type Execution_Event_Insert_Input = {
  content?: string | null | undefined;
  created_at?: unknown;
  event_type?: string | null | undefined;
  execution_graph?: Execution_Graph_Obj_Rel_Insert_Input | null | undefined;
  execution_node?: Execution_Node_Obj_Rel_Insert_Input | null | undefined;
  graph_id?: unknown;
  id?: unknown;
  node_id?: unknown;
  payload?: unknown;
  sequence?: unknown;
  status?: string | null | undefined;
};

/** on_conflict condition type for table "execution_event" */
export type Execution_Event_On_Conflict = {
  constraint: Execution_Event_Constraint;
  update_columns?: Array<Execution_Event_Update_Column>;
  where?: Execution_Event_Bool_Exp | null | undefined;
};

/** select columns of table "execution_event" */
export type Execution_Event_Select_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'event_type'
  /** column name */
  | 'graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'node_id'
  /** column name */
  | 'payload'
  /** column name */
  | 'sequence'
  /** column name */
  | 'status';

/** update columns of table "execution_event" */
export type Execution_Event_Update_Column =
  /** column name */
  | 'content'
  /** column name */
  | 'created_at'
  /** column name */
  | 'event_type'
  /** column name */
  | 'graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'node_id'
  /** column name */
  | 'payload'
  /** column name */
  | 'sequence'
  /** column name */
  | 'status';

export type Execution_Graph_Aggregate_Bool_Exp = {
  count?: Execution_Graph_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Execution_Graph_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Execution_Graph_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Execution_Graph_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "execution_graph" */
export type Execution_Graph_Aggregate_Order_By = {
  avg?: Execution_Graph_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Execution_Graph_Max_Order_By | null | undefined;
  min?: Execution_Graph_Min_Order_By | null | undefined;
  stddev?: Execution_Graph_Stddev_Order_By | null | undefined;
  stddev_pop?: Execution_Graph_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Execution_Graph_Stddev_Samp_Order_By | null | undefined;
  sum?: Execution_Graph_Sum_Order_By | null | undefined;
  var_pop?: Execution_Graph_Var_Pop_Order_By | null | undefined;
  var_samp?: Execution_Graph_Var_Samp_Order_By | null | undefined;
  variance?: Execution_Graph_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "execution_graph" */
export type Execution_Graph_Arr_Rel_Insert_Input = {
  data: Array<Execution_Graph_Insert_Input>;
  /** upsert condition */
  on_conflict?: Execution_Graph_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "execution_graph" */
export type Execution_Graph_Avg_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "execution_graph". All fields are combined with a logical 'AND'. */
export type Execution_Graph_Bool_Exp = {
  _and?: Array<Execution_Graph_Bool_Exp> | null | undefined;
  _not?: Execution_Graph_Bool_Exp | null | undefined;
  _or?: Array<Execution_Graph_Bool_Exp> | null | undefined;
  ai_assistant_thread?: Ai_Assistant_Thread_Bool_Exp | null | undefined;
  assistant_id?: String_Comparison_Exp | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  execution_artifacts?: Execution_Artifact_Bool_Exp | null | undefined;
  execution_artifacts_aggregate?: Execution_Artifact_Aggregate_Bool_Exp | null | undefined;
  execution_events?: Execution_Event_Bool_Exp | null | undefined;
  execution_events_aggregate?: Execution_Event_Aggregate_Bool_Exp | null | undefined;
  execution_nodes?: Execution_Node_Bool_Exp | null | undefined;
  execution_nodes_aggregate?: Execution_Node_Aggregate_Bool_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  metadata?: Jsonb_Comparison_Exp | null | undefined;
  run_id?: String_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  thread_id?: Bigint_Comparison_Exp | null | undefined;
  title?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "execution_graph" */
export type Execution_Graph_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'execution_graph_pkey';

/** input type for inserting data into table "execution_graph" */
export type Execution_Graph_Insert_Input = {
  ai_assistant_thread?: Ai_Assistant_Thread_Obj_Rel_Insert_Input | null | undefined;
  assistant_id?: string | null | undefined;
  completed_at?: unknown;
  execution_artifacts?: Execution_Artifact_Arr_Rel_Insert_Input | null | undefined;
  execution_events?: Execution_Event_Arr_Rel_Insert_Input | null | undefined;
  execution_nodes?: Execution_Node_Arr_Rel_Insert_Input | null | undefined;
  id?: unknown;
  metadata?: unknown;
  run_id?: string | null | undefined;
  started_at?: unknown;
  status?: string | null | undefined;
  thread_id?: unknown;
  title?: string | null | undefined;
  updated_at?: unknown;
};

/** order by max() on columns of table "execution_graph" */
export type Execution_Graph_Max_Order_By = {
  assistant_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  run_id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** order by min() on columns of table "execution_graph" */
export type Execution_Graph_Min_Order_By = {
  assistant_id?: Order_By | null | undefined;
  completed_at?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  run_id?: Order_By | null | undefined;
  started_at?: Order_By | null | undefined;
  status?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
  title?: Order_By | null | undefined;
  updated_at?: Order_By | null | undefined;
};

/** input type for inserting object relation for remote table "execution_graph" */
export type Execution_Graph_Obj_Rel_Insert_Input = {
  data: Execution_Graph_Insert_Input;
  /** upsert condition */
  on_conflict?: Execution_Graph_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "execution_graph" */
export type Execution_Graph_On_Conflict = {
  constraint: Execution_Graph_Constraint;
  update_columns?: Array<Execution_Graph_Update_Column>;
  where?: Execution_Graph_Bool_Exp | null | undefined;
};

/** select columns of table "execution_graph" */
export type Execution_Graph_Select_Column =
  /** column name */
  | 'assistant_id'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'id'
  /** column name */
  | 'metadata'
  /** column name */
  | 'run_id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'title'
  /** column name */
  | 'updated_at';

/** order by stddev() on columns of table "execution_graph" */
export type Execution_Graph_Stddev_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "execution_graph" */
export type Execution_Graph_Stddev_Pop_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "execution_graph" */
export type Execution_Graph_Stddev_Samp_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by sum() on columns of table "execution_graph" */
export type Execution_Graph_Sum_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** update columns of table "execution_graph" */
export type Execution_Graph_Update_Column =
  /** column name */
  | 'assistant_id'
  /** column name */
  | 'completed_at'
  /** column name */
  | 'id'
  /** column name */
  | 'metadata'
  /** column name */
  | 'run_id'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'thread_id'
  /** column name */
  | 'title'
  /** column name */
  | 'updated_at';

/** order by var_pop() on columns of table "execution_graph" */
export type Execution_Graph_Var_Pop_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "execution_graph" */
export type Execution_Graph_Var_Samp_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

/** order by variance() on columns of table "execution_graph" */
export type Execution_Graph_Variance_Order_By = {
  id?: Order_By | null | undefined;
  thread_id?: Order_By | null | undefined;
};

export type Execution_Node_Aggregate_Bool_Exp = {
  count?: Execution_Node_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Execution_Node_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Execution_Node_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Execution_Node_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** input type for inserting array relation for remote table "execution_node" */
export type Execution_Node_Arr_Rel_Insert_Input = {
  data: Array<Execution_Node_Insert_Input>;
  /** upsert condition */
  on_conflict?: Execution_Node_On_Conflict | null | undefined;
};

/** Boolean expression to filter rows from the table "execution_node". All fields are combined with a logical 'AND'. */
export type Execution_Node_Bool_Exp = {
  _and?: Array<Execution_Node_Bool_Exp> | null | undefined;
  _not?: Execution_Node_Bool_Exp | null | undefined;
  _or?: Array<Execution_Node_Bool_Exp> | null | undefined;
  completed_at?: Timestamptz_Comparison_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  error?: Jsonb_Comparison_Exp | null | undefined;
  execution_artifacts?: Execution_Artifact_Bool_Exp | null | undefined;
  execution_artifacts_aggregate?: Execution_Artifact_Aggregate_Bool_Exp | null | undefined;
  execution_events?: Execution_Event_Bool_Exp | null | undefined;
  execution_events_aggregate?: Execution_Event_Aggregate_Bool_Exp | null | undefined;
  execution_graph?: Execution_Graph_Bool_Exp | null | undefined;
  execution_node?: Execution_Node_Bool_Exp | null | undefined;
  execution_nodes?: Execution_Node_Bool_Exp | null | undefined;
  execution_nodes_aggregate?: Execution_Node_Aggregate_Bool_Exp | null | undefined;
  external_task_id?: String_Comparison_Exp | null | undefined;
  graph_id?: Bigint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  input?: Jsonb_Comparison_Exp | null | undefined;
  kind?: String_Comparison_Exp | null | undefined;
  metadata?: Jsonb_Comparison_Exp | null | undefined;
  name?: String_Comparison_Exp | null | undefined;
  output?: Jsonb_Comparison_Exp | null | undefined;
  parent_id?: Bigint_Comparison_Exp | null | undefined;
  sequence?: Bigint_Comparison_Exp | null | undefined;
  started_at?: Timestamptz_Comparison_Exp | null | undefined;
  status?: String_Comparison_Exp | null | undefined;
  tool_call_id?: String_Comparison_Exp | null | undefined;
  updated_at?: Timestamptz_Comparison_Exp | null | undefined;
  wait_reason?: String_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "execution_node" */
export type Execution_Node_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'execution_node_pkey'
  /** unique or primary key constraint on columns "graph_id", "sequence" */
  | 'uniq_exec_node_graph_seq';

/** input type for inserting data into table "execution_node" */
export type Execution_Node_Insert_Input = {
  completed_at?: unknown;
  created_at?: unknown;
  error?: unknown;
  execution_artifacts?: Execution_Artifact_Arr_Rel_Insert_Input | null | undefined;
  execution_events?: Execution_Event_Arr_Rel_Insert_Input | null | undefined;
  execution_graph?: Execution_Graph_Obj_Rel_Insert_Input | null | undefined;
  execution_node?: Execution_Node_Obj_Rel_Insert_Input | null | undefined;
  execution_nodes?: Execution_Node_Arr_Rel_Insert_Input | null | undefined;
  external_task_id?: string | null | undefined;
  graph_id?: unknown;
  id?: unknown;
  input?: unknown;
  kind?: string | null | undefined;
  metadata?: unknown;
  name?: string | null | undefined;
  output?: unknown;
  parent_id?: unknown;
  sequence?: unknown;
  started_at?: unknown;
  status?: string | null | undefined;
  tool_call_id?: string | null | undefined;
  updated_at?: unknown;
  wait_reason?: string | null | undefined;
};

/** input type for inserting object relation for remote table "execution_node" */
export type Execution_Node_Obj_Rel_Insert_Input = {
  data: Execution_Node_Insert_Input;
  /** upsert condition */
  on_conflict?: Execution_Node_On_Conflict | null | undefined;
};

/** on_conflict condition type for table "execution_node" */
export type Execution_Node_On_Conflict = {
  constraint: Execution_Node_Constraint;
  update_columns?: Array<Execution_Node_Update_Column>;
  where?: Execution_Node_Bool_Exp | null | undefined;
};

/** select columns of table "execution_node" */
export type Execution_Node_Select_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error'
  /** column name */
  | 'external_task_id'
  /** column name */
  | 'graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'input'
  /** column name */
  | 'kind'
  /** column name */
  | 'metadata'
  /** column name */
  | 'name'
  /** column name */
  | 'output'
  /** column name */
  | 'parent_id'
  /** column name */
  | 'sequence'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'tool_call_id'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'wait_reason';

/** update columns of table "execution_node" */
export type Execution_Node_Update_Column =
  /** column name */
  | 'completed_at'
  /** column name */
  | 'created_at'
  /** column name */
  | 'error'
  /** column name */
  | 'external_task_id'
  /** column name */
  | 'graph_id'
  /** column name */
  | 'id'
  /** column name */
  | 'input'
  /** column name */
  | 'kind'
  /** column name */
  | 'metadata'
  /** column name */
  | 'name'
  /** column name */
  | 'output'
  /** column name */
  | 'parent_id'
  /** column name */
  | 'sequence'
  /** column name */
  | 'started_at'
  /** column name */
  | 'status'
  /** column name */
  | 'tool_call_id'
  /** column name */
  | 'updated_at'
  /** column name */
  | 'wait_reason';

/** Boolean expression to compare columns of type "float8". All fields are combined with logical 'AND'. */
export type Float8_Comparison_Exp = {
  _eq?: unknown;
  _gt?: unknown;
  _gte?: unknown;
  _in?: Array<unknown> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: unknown;
  _lte?: unknown;
  _neq?: unknown;
  _nin?: Array<unknown> | null | undefined;
};

/** Boolean expression to compare columns of type "inet". All fields are combined with logical 'AND'. */
export type Inet_Comparison_Exp = {
  _eq?: unknown;
  _gt?: unknown;
  _gte?: unknown;
  _in?: Array<unknown> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: unknown;
  _lte?: unknown;
  _neq?: unknown;
  _nin?: Array<unknown> | null | undefined;
};

export type Jsonb_Cast_Exp = {
  String?: String_Comparison_Exp | null | undefined;
};

/** Boolean expression to compare columns of type "jsonb". All fields are combined with logical 'AND'. */
export type Jsonb_Comparison_Exp = {
  _cast?: Jsonb_Cast_Exp | null | undefined;
  /** is the column contained in the given json value */
  _contained_in?: unknown;
  /** does the column contain the given json value at the top level */
  _contains?: unknown;
  _eq?: unknown;
  _gt?: unknown;
  _gte?: unknown;
  /** does the string exist as a top-level key in the column */
  _has_key?: string | null | undefined;
  /** do all of these strings exist as top-level keys in the column */
  _has_keys_all?: Array<string> | null | undefined;
  /** do any of these strings exist as top-level keys in the column */
  _has_keys_any?: Array<string> | null | undefined;
  _in?: Array<unknown> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: unknown;
  _lte?: unknown;
  _neq?: unknown;
  _nin?: Array<unknown> | null | undefined;
};

export type Mission_Review_Aggregate_Bool_Exp = {
  bool_and?: Mission_Review_Aggregate_Bool_Exp_Bool_And | null | undefined;
  bool_or?: Mission_Review_Aggregate_Bool_Exp_Bool_Or | null | undefined;
  count?: Mission_Review_Aggregate_Bool_Exp_Count | null | undefined;
};

export type Mission_Review_Aggregate_Bool_Exp_Bool_And = {
  arguments: Mission_Review_Select_Column_Mission_Review_Aggregate_Bool_Exp_Bool_And_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Mission_Review_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Mission_Review_Aggregate_Bool_Exp_Bool_Or = {
  arguments: Mission_Review_Select_Column_Mission_Review_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns;
  distinct?: boolean | null | undefined;
  filter?: Mission_Review_Bool_Exp | null | undefined;
  predicate: Boolean_Comparison_Exp;
};

export type Mission_Review_Aggregate_Bool_Exp_Count = {
  arguments?: Array<Mission_Review_Select_Column> | null | undefined;
  distinct?: boolean | null | undefined;
  filter?: Mission_Review_Bool_Exp | null | undefined;
  predicate: Int_Comparison_Exp;
};

/** order by aggregate values of table "mission_review" */
export type Mission_Review_Aggregate_Order_By = {
  avg?: Mission_Review_Avg_Order_By | null | undefined;
  count?: Order_By | null | undefined;
  max?: Mission_Review_Max_Order_By | null | undefined;
  min?: Mission_Review_Min_Order_By | null | undefined;
  stddev?: Mission_Review_Stddev_Order_By | null | undefined;
  stddev_pop?: Mission_Review_Stddev_Pop_Order_By | null | undefined;
  stddev_samp?: Mission_Review_Stddev_Samp_Order_By | null | undefined;
  sum?: Mission_Review_Sum_Order_By | null | undefined;
  var_pop?: Mission_Review_Var_Pop_Order_By | null | undefined;
  var_samp?: Mission_Review_Var_Samp_Order_By | null | undefined;
  variance?: Mission_Review_Variance_Order_By | null | undefined;
};

/** input type for inserting array relation for remote table "mission_review" */
export type Mission_Review_Arr_Rel_Insert_Input = {
  data: Array<Mission_Review_Insert_Input>;
  /** upsert condition */
  on_conflict?: Mission_Review_On_Conflict | null | undefined;
};

/** order by avg() on columns of table "mission_review" */
export type Mission_Review_Avg_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** Boolean expression to filter rows from the table "mission_review". All fields are combined with a logical 'AND'. */
export type Mission_Review_Bool_Exp = {
  _and?: Array<Mission_Review_Bool_Exp> | null | undefined;
  _not?: Mission_Review_Bool_Exp | null | undefined;
  _or?: Array<Mission_Review_Bool_Exp> | null | undefined;
  confidence_score?: Smallint_Comparison_Exp | null | undefined;
  confirmed_vuln_count?: Smallint_Comparison_Exp | null | undefined;
  core_overview?: Core_Overview_Bool_Exp | null | undefined;
  created_at?: Timestamptz_Comparison_Exp | null | undefined;
  has_poc_evidence?: Boolean_Comparison_Exp | null | undefined;
  high_severity_count?: Smallint_Comparison_Exp | null | undefined;
  id?: Bigint_Comparison_Exp | null | undefined;
  needs_human_review?: Boolean_Comparison_Exp | null | undefined;
  overview_id?: Bigint_Comparison_Exp | null | undefined;
  reasoning?: String_Comparison_Exp | null | undefined;
  rejection_reasons?: Jsonb_Comparison_Exp | null | undefined;
  reviewed_at?: Timestamptz_Comparison_Exp | null | undefined;
  scan_coverage_pct?: Smallint_Comparison_Exp | null | undefined;
  suggested_actions?: Jsonb_Comparison_Exp | null | undefined;
  triggered_by?: String_Comparison_Exp | null | undefined;
  triggered_by_agent?: String_Comparison_Exp | null | undefined;
  verdict?: String_Comparison_Exp | null | undefined;
  vuln_count?: Smallint_Comparison_Exp | null | undefined;
};

/** unique or primary key constraints on table "mission_review" */
export type Mission_Review_Constraint =
  /** unique or primary key constraint on columns "id" */
  | 'mission_review_pkey';

/** input type for inserting data into table "mission_review" */
export type Mission_Review_Insert_Input = {
  confidence_score?: unknown;
  confirmed_vuln_count?: unknown;
  core_overview?: Core_Overview_Obj_Rel_Insert_Input | null | undefined;
  created_at?: unknown;
  has_poc_evidence?: boolean | null | undefined;
  high_severity_count?: unknown;
  id?: unknown;
  needs_human_review?: boolean | null | undefined;
  overview_id?: unknown;
  reasoning?: string | null | undefined;
  rejection_reasons?: unknown;
  reviewed_at?: unknown;
  scan_coverage_pct?: unknown;
  suggested_actions?: unknown;
  triggered_by?: string | null | undefined;
  triggered_by_agent?: string | null | undefined;
  verdict?: string | null | undefined;
  vuln_count?: unknown;
};

/** order by max() on columns of table "mission_review" */
export type Mission_Review_Max_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  reasoning?: Order_By | null | undefined;
  reviewed_at?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  triggered_by?: Order_By | null | undefined;
  triggered_by_agent?: Order_By | null | undefined;
  verdict?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** order by min() on columns of table "mission_review" */
export type Mission_Review_Min_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  reasoning?: Order_By | null | undefined;
  reviewed_at?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  triggered_by?: Order_By | null | undefined;
  triggered_by_agent?: Order_By | null | undefined;
  verdict?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** on_conflict condition type for table "mission_review" */
export type Mission_Review_On_Conflict = {
  constraint: Mission_Review_Constraint;
  update_columns?: Array<Mission_Review_Update_Column>;
  where?: Mission_Review_Bool_Exp | null | undefined;
};

/** Ordering options when selecting data from "mission_review". */
export type Mission_Review_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  core_overview?: Core_Overview_Order_By | null | undefined;
  created_at?: Order_By | null | undefined;
  has_poc_evidence?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  needs_human_review?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  reasoning?: Order_By | null | undefined;
  rejection_reasons?: Order_By | null | undefined;
  reviewed_at?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  suggested_actions?: Order_By | null | undefined;
  triggered_by?: Order_By | null | undefined;
  triggered_by_agent?: Order_By | null | undefined;
  verdict?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** select columns of table "mission_review" */
export type Mission_Review_Select_Column =
  /** column name */
  | 'confidence_score'
  /** column name */
  | 'confirmed_vuln_count'
  /** column name */
  | 'created_at'
  /** column name */
  | 'has_poc_evidence'
  /** column name */
  | 'high_severity_count'
  /** column name */
  | 'id'
  /** column name */
  | 'needs_human_review'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'reasoning'
  /** column name */
  | 'rejection_reasons'
  /** column name */
  | 'reviewed_at'
  /** column name */
  | 'scan_coverage_pct'
  /** column name */
  | 'suggested_actions'
  /** column name */
  | 'triggered_by'
  /** column name */
  | 'triggered_by_agent'
  /** column name */
  | 'verdict'
  /** column name */
  | 'vuln_count';

/** select "mission_review_aggregate_bool_exp_bool_and_arguments_columns" columns of table "mission_review" */
export type Mission_Review_Select_Column_Mission_Review_Aggregate_Bool_Exp_Bool_And_Arguments_Columns =
  /** column name */
  | 'has_poc_evidence'
  /** column name */
  | 'needs_human_review';

/** select "mission_review_aggregate_bool_exp_bool_or_arguments_columns" columns of table "mission_review" */
export type Mission_Review_Select_Column_Mission_Review_Aggregate_Bool_Exp_Bool_Or_Arguments_Columns =
  /** column name */
  | 'has_poc_evidence'
  /** column name */
  | 'needs_human_review';

/** order by stddev() on columns of table "mission_review" */
export type Mission_Review_Stddev_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** order by stddev_pop() on columns of table "mission_review" */
export type Mission_Review_Stddev_Pop_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** order by stddev_samp() on columns of table "mission_review" */
export type Mission_Review_Stddev_Samp_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** order by sum() on columns of table "mission_review" */
export type Mission_Review_Sum_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** update columns of table "mission_review" */
export type Mission_Review_Update_Column =
  /** column name */
  | 'confidence_score'
  /** column name */
  | 'confirmed_vuln_count'
  /** column name */
  | 'created_at'
  /** column name */
  | 'has_poc_evidence'
  /** column name */
  | 'high_severity_count'
  /** column name */
  | 'id'
  /** column name */
  | 'needs_human_review'
  /** column name */
  | 'overview_id'
  /** column name */
  | 'reasoning'
  /** column name */
  | 'rejection_reasons'
  /** column name */
  | 'reviewed_at'
  /** column name */
  | 'scan_coverage_pct'
  /** column name */
  | 'suggested_actions'
  /** column name */
  | 'triggered_by'
  /** column name */
  | 'triggered_by_agent'
  /** column name */
  | 'verdict'
  /** column name */
  | 'vuln_count';

/** order by var_pop() on columns of table "mission_review" */
export type Mission_Review_Var_Pop_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** order by var_samp() on columns of table "mission_review" */
export type Mission_Review_Var_Samp_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** order by variance() on columns of table "mission_review" */
export type Mission_Review_Variance_Order_By = {
  confidence_score?: Order_By | null | undefined;
  confirmed_vuln_count?: Order_By | null | undefined;
  high_severity_count?: Order_By | null | undefined;
  id?: Order_By | null | undefined;
  overview_id?: Order_By | null | undefined;
  scan_coverage_pct?: Order_By | null | undefined;
  vuln_count?: Order_By | null | undefined;
};

/** column ordering options */
export type Order_By =
  /** in ascending order, nulls last */
  | 'asc'
  /** in ascending order, nulls first */
  | 'asc_nulls_first'
  /** in ascending order, nulls last */
  | 'asc_nulls_last'
  /** in descending order, nulls first */
  | 'desc'
  /** in descending order, nulls first */
  | 'desc_nulls_first'
  /** in descending order, nulls last */
  | 'desc_nulls_last';

/** Boolean expression to compare columns of type "smallint". All fields are combined with logical 'AND'. */
export type Smallint_Comparison_Exp = {
  _eq?: unknown;
  _gt?: unknown;
  _gte?: unknown;
  _in?: Array<unknown> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: unknown;
  _lte?: unknown;
  _neq?: unknown;
  _nin?: Array<unknown> | null | undefined;
};

/** Boolean expression to compare columns of type "timestamptz". All fields are combined with logical 'AND'. */
export type Timestamptz_Comparison_Exp = {
  _eq?: unknown;
  _gt?: unknown;
  _gte?: unknown;
  _in?: Array<unknown> | null | undefined;
  _is_null?: boolean | null | undefined;
  _lt?: unknown;
  _lte?: unknown;
  _neq?: unknown;
  _nin?: Array<unknown> | null | undefined;
};

export type GetAttackPlansQueryVariables = Exact<{
  where?: Core_Attackplan_Bool_Exp | null | undefined;
  orderBy?: Array<Core_Attackplan_Order_By> | Core_Attackplan_Order_By | null | undefined;
  limit?: number | null | undefined;
  offset?: number | null | undefined;
}>;


export type GetAttackPlansQuery = { core_attackplan: Array<{ id: unknown, target_id: unknown, thread_id: unknown, objective: string, scope: unknown, status: string, parent_plan_id: unknown, created_at: unknown, updated_at: unknown }>, core_attackplan_aggregate: { aggregate: { count: number } | null } };

export type GetAttackPlanQueryVariables = Exact<{
  id: unknown;
}>;


export type GetAttackPlanQuery = { core_attackplan_by_pk: { id: unknown, target_id: unknown, thread_id: unknown, objective: string, scope: unknown, status: string, parent_plan_id: unknown, created_at: unknown, updated_at: unknown, core_actions: Array<{ id: unknown, target_id: unknown, plan_id: unknown, purpose: unknown, purpose_text: string | null, status: string, agent_thread_id: unknown, agent_role: string | null, execution_graph_id: unknown, result_summary: string | null, order: number, created_at: unknown, started_at: unknown, completed_at: unknown }> } | null };

export type CreateAttackPlanMutationVariables = Exact<{
  object: Core_Attackplan_Insert_Input;
}>;


export type CreateAttackPlanMutation = { insert_core_attackplan_one: { id: unknown, target_id: unknown, thread_id: unknown, objective: string, scope: unknown, status: string, parent_plan_id: unknown, created_at: unknown, updated_at: unknown } | null };

export type UpdateAttackPlanMutationVariables = Exact<{
  id: unknown;
  updates: Core_Attackplan_Set_Input;
}>;


export type UpdateAttackPlanMutation = { update_core_attackplan_by_pk: { id: unknown, target_id: unknown, thread_id: unknown, objective: string, scope: unknown, status: string, parent_plan_id: unknown, created_at: unknown, updated_at: unknown } | null };

export type GetPlanActionsQueryVariables = Exact<{
  where?: Core_Action_Bool_Exp | null | undefined;
  orderBy?: Array<Core_Action_Order_By> | Core_Action_Order_By | null | undefined;
  limit?: number | null | undefined;
  offset?: number | null | undefined;
}>;


export type GetPlanActionsQuery = { core_action: Array<{ id: unknown, target_id: unknown, plan_id: unknown, purpose: unknown, purpose_text: string | null, status: string, agent_thread_id: unknown, agent_role: string | null, execution_graph_id: unknown, result_summary: string | null, order: number, created_at: unknown, started_at: unknown, completed_at: unknown }>, core_action_aggregate: { aggregate: { count: number } | null } };

export type GetActionQueryVariables = Exact<{
  id: unknown;
}>;


export type GetActionQuery = { core_action_by_pk: { id: unknown, target_id: unknown, plan_id: unknown, purpose: unknown, purpose_text: string | null, status: string, agent_thread_id: unknown, agent_role: string | null, execution_graph_id: unknown, result_summary: string | null, order: number, created_at: unknown, started_at: unknown, completed_at: unknown } | null };

export type UpdateActionMutationVariables = Exact<{
  id: unknown;
  updates: Core_Action_Set_Input;
}>;


export type UpdateActionMutation = { update_core_action_by_pk: { id: unknown, target_id: unknown, plan_id: unknown, purpose: unknown, purpose_text: string | null, status: string, result_summary: string | null, order: number, created_at: unknown, started_at: unknown, completed_at: unknown } | null };

export type GetAttackVectorsQueryVariables = Exact<{
  where?: Core_Attackvector_Bool_Exp | null | undefined;
  orderBy?: Array<Core_Attackvector_Order_By> | Core_Attackvector_Order_By | null | undefined;
  limit?: number | null | undefined;
  offset?: number | null | undefined;
}>;


export type GetAttackVectorsQuery = { core_attackvector: Array<{ id: unknown, overview_id: unknown, name: string, description: string | null, vector_type: string, status: string, risk_score: unknown, evidence: string | null, created_at: unknown, updated_at: unknown }>, core_attackvector_aggregate: { aggregate: { count: number } | null } };

export type GetAttackVectorQueryVariables = Exact<{
  id: unknown;
}>;


export type GetAttackVectorQuery = { core_attackvector_by_pk: { id: unknown, overview_id: unknown, name: string, description: string | null, vector_type: string, status: string, risk_score: unknown, evidence: string | null, created_at: unknown, updated_at: unknown } | null };

export type UpdateAttackVectorMutationVariables = Exact<{
  id: unknown;
  updates: Core_Attackvector_Set_Input;
}>;


export type UpdateAttackVectorMutation = { update_core_attackvector_by_pk: { id: unknown, overview_id: unknown, name: string, description: string | null, vector_type: string, status: string, risk_score: unknown, evidence: string | null, created_at: unknown, updated_at: unknown } | null };

export type GetMissionReviewsByOverviewQueryVariables = Exact<{
  overviewId: unknown;
}>;


export type GetMissionReviewsByOverviewQuery = { mission_review: Array<{ id: unknown, overview_id: unknown, verdict: string, confidence_score: unknown, reasoning: string, rejection_reasons: unknown, suggested_actions: unknown, needs_human_review: boolean, vuln_count: unknown, confirmed_vuln_count: unknown, high_severity_count: unknown, has_poc_evidence: boolean, scan_coverage_pct: unknown, triggered_by: string, triggered_by_agent: string, reviewed_at: unknown, created_at: unknown }> };

export type GetMissionReviewQueryVariables = Exact<{
  id: unknown;
}>;


export type GetMissionReviewQuery = { mission_review_by_pk: { id: unknown, overview_id: unknown, verdict: string, confidence_score: unknown, reasoning: string, rejection_reasons: unknown, suggested_actions: unknown, needs_human_review: boolean, vuln_count: unknown, confirmed_vuln_count: unknown, high_severity_count: unknown, has_poc_evidence: boolean, scan_coverage_pct: unknown, triggered_by: string, triggered_by_agent: string, reviewed_at: unknown, created_at: unknown } | null };

export type GetMissionReviewsQueryVariables = Exact<{
  where?: Mission_Review_Bool_Exp | null | undefined;
  orderBy?: Array<Mission_Review_Order_By> | Mission_Review_Order_By | null | undefined;
  limit?: number | null | undefined;
}>;


export type GetMissionReviewsQuery = { mission_review: Array<{ id: unknown, overview_id: unknown, verdict: string, confidence_score: unknown, reasoning: string, needs_human_review: boolean, vuln_count: unknown, confirmed_vuln_count: unknown, high_severity_count: unknown, has_poc_evidence: boolean, scan_coverage_pct: unknown, triggered_by: string, triggered_by_agent: string, reviewed_at: unknown, created_at: unknown }> };

export type AddSeedMutationVariables = Exact<{
  object: Core_Seed_Insert_Input;
}>;


export type AddSeedMutation = { insert_core_seed_one: { id: unknown, target_id: unknown, value: string, type: string, is_active: boolean, created_at: unknown } | null };

export type DeleteSeedMutationVariables = Exact<{
  id: unknown;
}>;


export type DeleteSeedMutation = { delete_core_seed_by_pk: { id: unknown } | null };

export type CreateTargetMutationVariables = Exact<{
  object: Core_Target_Insert_Input;
}>;


export type CreateTargetMutation = { insert_core_target_one: { id: unknown, name: string, description: string | null, created_at: unknown } | null };

export type UpdateTargetMutationVariables = Exact<{
  id: unknown;
  updates: Core_Target_Set_Input;
}>;


export type UpdateTargetMutation = { update_core_target_by_pk: { id: unknown, name: string, description: string | null, created_at: unknown } | null };

export type DeleteTargetMutationVariables = Exact<{
  id: unknown;
}>;


export type DeleteTargetMutation = { delete_core_target_by_pk: { id: unknown } | null };

export type GetVulnerabilitiesQueryVariables = Exact<{
  where?: Core_Vulnerability_Bool_Exp | null | undefined;
  orderBy?: Array<Core_Vulnerability_Order_By> | Core_Vulnerability_Order_By | null | undefined;
  limit?: number | null | undefined;
  offset?: number | null | undefined;
}>;


export type GetVulnerabilitiesQuery = { core_vulnerability: Array<{ id: unknown, target_id: unknown, ip_asset_id: unknown, subdomain_asset_id: unknown, url_asset_id: unknown, source_attack_vector_id: unknown, action_id: unknown, overview_id: unknown, cve_intelligence_id: unknown, enrichment_status: string, enrichment_attempted_at: unknown, tool_source: string, template_id: string, name: string, severity: string, matched_at: string, extracted_results: unknown, request_raw: string | null, response_raw: string | null, fingerprint: string, status: string, description: string | null, remediation: string | null, last_seen: unknown, created_at: unknown, updated_at: unknown, core_target: { id: unknown, name: string } | null }>, core_vulnerability_aggregate: { aggregate: { count: number } | null } };

export type GetVulnerabilityQueryVariables = Exact<{
  id: unknown;
}>;


export type GetVulnerabilityQuery = { core_vulnerability_by_pk: { id: unknown, target_id: unknown, ip_asset_id: unknown, subdomain_asset_id: unknown, url_asset_id: unknown, source_attack_vector_id: unknown, action_id: unknown, overview_id: unknown, cve_intelligence_id: unknown, enrichment_status: string, enrichment_attempted_at: unknown, tool_source: string, template_id: string, name: string, severity: string, matched_at: string, extracted_results: unknown, request_raw: string | null, response_raw: string | null, fingerprint: string, status: string, description: string | null, remediation: string | null, last_seen: unknown, created_at: unknown, updated_at: unknown, core_target: { id: unknown, name: string } | null, core_pocrecords: Array<{ id: unknown, vulnerability_id: unknown, title: string, content: string, language: string, result: string | null, is_verified: boolean, created_at: unknown, updated_at: unknown }> } | null };

export type GetVulnerabilityCountsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetVulnerabilityCountsQuery = { core_vulnerability_aggregate: { aggregate: { count: number } | null }, critical: { aggregate: { count: number } | null }, high: { aggregate: { count: number } | null }, medium: { aggregate: { count: number } | null }, low: { aggregate: { count: number } | null }, info: { aggregate: { count: number } | null } };

export type CreateVulnerabilityMutationVariables = Exact<{
  object: Core_Vulnerability_Insert_Input;
}>;


export type CreateVulnerabilityMutation = { insert_core_vulnerability_one: { id: unknown, target_id: unknown, name: string, severity: string, template_id: string, matched_at: string, tool_source: string, status: string, description: string | null, remediation: string | null, created_at: unknown } | null };

export type UpdateVulnerabilityMutationVariables = Exact<{
  id: unknown;
  updates: Core_Vulnerability_Set_Input;
}>;


export type UpdateVulnerabilityMutation = { update_core_vulnerability_by_pk: { id: unknown, target_id: unknown, name: string, severity: string, status: string, description: string | null, remediation: string | null, updated_at: unknown } | null };

export type DeleteVulnerabilityMutationVariables = Exact<{
  id: unknown;
}>;


export type DeleteVulnerabilityMutation = { delete_core_vulnerability_by_pk: { id: unknown } | null };

export type BatchUpdateVulnerabilityStatusMutationVariables = Exact<{
  ids: Array<unknown> | unknown;
  status: string;
}>;


export type BatchUpdateVulnerabilityStatusMutation = { update_core_vulnerability_many: Array<{ affected_rows: number } | null> | null };

export type BatchDeleteVulnerabilitiesMutationVariables = Exact<{
  ids: Array<unknown> | unknown;
}>;


export type BatchDeleteVulnerabilitiesMutation = { delete_core_vulnerability: { affected_rows: number } | null };

export type GetPoCsQueryVariables = Exact<{
  vulnId: unknown;
}>;


export type GetPoCsQuery = { core_pocrecord: Array<{ id: unknown, vulnerability_id: unknown, title: string, content: string, language: string, result: string | null, is_verified: boolean, created_at: unknown, updated_at: unknown }> };

export type CreatePoCMutationVariables = Exact<{
  object: Core_Pocrecord_Insert_Input;
}>;


export type CreatePoCMutation = { insert_core_pocrecord_one: { id: unknown, vulnerability_id: unknown, title: string, content: string, language: string, result: string | null, is_verified: boolean, created_at: unknown, updated_at: unknown } | null };

export type UpdatePoCMutationVariables = Exact<{
  id: unknown;
  updates: Core_Pocrecord_Set_Input;
}>;


export type UpdatePoCMutation = { update_core_pocrecord_by_pk: { id: unknown, vulnerability_id: unknown, title: string, content: string, language: string, result: string | null, is_verified: boolean, created_at: unknown, updated_at: unknown } | null };

export type DeletePoCMutationVariables = Exact<{
  id: unknown;
}>;


export type DeletePoCMutation = { delete_core_pocrecord_by_pk: { id: unknown } | null };


export const GetAttackPlansDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetAttackPlans"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"where"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackplan_bool_exp"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}},"type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackplan_order_by"}}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"offset"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_attackplan"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}},{"kind":"Argument","name":{"kind":"Name","value":"offset"},"value":{"kind":"Variable","name":{"kind":"Name","value":"offset"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"objective"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"parent_plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}},{"kind":"Field","name":{"kind":"Name","value":"core_attackplan_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}}]}}]} as unknown as DocumentNode<GetAttackPlansQuery, GetAttackPlansQueryVariables>;
export const GetAttackPlanDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetAttackPlan"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_attackplan_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"objective"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"parent_plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}},{"kind":"Field","name":{"kind":"Name","value":"core_actions"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"order"},"value":{"kind":"EnumValue","value":"asc"}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"purpose"}},{"kind":"Field","name":{"kind":"Name","value":"purpose_text"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"agent_thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"agent_role"}},{"kind":"Field","name":{"kind":"Name","value":"execution_graph_id"}},{"kind":"Field","name":{"kind":"Name","value":"result_summary"}},{"kind":"Field","name":{"kind":"Name","value":"order"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"started_at"}},{"kind":"Field","name":{"kind":"Name","value":"completed_at"}}]}}]}}]}}]} as unknown as DocumentNode<GetAttackPlanQuery, GetAttackPlanQueryVariables>;
export const CreateAttackPlanDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateAttackPlan"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"object"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackplan_insert_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"insert_core_attackplan_one"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"object"},"value":{"kind":"Variable","name":{"kind":"Name","value":"object"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"objective"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"parent_plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<CreateAttackPlanMutation, CreateAttackPlanMutationVariables>;
export const UpdateAttackPlanDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateAttackPlan"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"updates"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackplan_set_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_attackplan_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"pk_columns"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}},{"kind":"Argument","name":{"kind":"Name","value":"_set"},"value":{"kind":"Variable","name":{"kind":"Name","value":"updates"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"objective"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"parent_plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<UpdateAttackPlanMutation, UpdateAttackPlanMutationVariables>;
export const GetPlanActionsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetPlanActions"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"where"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"core_action_bool_exp"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}},"type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_action_order_by"}}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"offset"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_action"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}},{"kind":"Argument","name":{"kind":"Name","value":"offset"},"value":{"kind":"Variable","name":{"kind":"Name","value":"offset"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"purpose"}},{"kind":"Field","name":{"kind":"Name","value":"purpose_text"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"agent_thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"agent_role"}},{"kind":"Field","name":{"kind":"Name","value":"execution_graph_id"}},{"kind":"Field","name":{"kind":"Name","value":"result_summary"}},{"kind":"Field","name":{"kind":"Name","value":"order"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"started_at"}},{"kind":"Field","name":{"kind":"Name","value":"completed_at"}}]}},{"kind":"Field","name":{"kind":"Name","value":"core_action_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}}]}}]} as unknown as DocumentNode<GetPlanActionsQuery, GetPlanActionsQueryVariables>;
export const GetActionDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetAction"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_action_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"purpose"}},{"kind":"Field","name":{"kind":"Name","value":"purpose_text"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"agent_thread_id"}},{"kind":"Field","name":{"kind":"Name","value":"agent_role"}},{"kind":"Field","name":{"kind":"Name","value":"execution_graph_id"}},{"kind":"Field","name":{"kind":"Name","value":"result_summary"}},{"kind":"Field","name":{"kind":"Name","value":"order"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"started_at"}},{"kind":"Field","name":{"kind":"Name","value":"completed_at"}}]}}]}}]} as unknown as DocumentNode<GetActionQuery, GetActionQueryVariables>;
export const UpdateActionDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateAction"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"updates"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_action_set_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_action_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"pk_columns"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}},{"kind":"Argument","name":{"kind":"Name","value":"_set"},"value":{"kind":"Variable","name":{"kind":"Name","value":"updates"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"plan_id"}},{"kind":"Field","name":{"kind":"Name","value":"purpose"}},{"kind":"Field","name":{"kind":"Name","value":"purpose_text"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"result_summary"}},{"kind":"Field","name":{"kind":"Name","value":"order"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"started_at"}},{"kind":"Field","name":{"kind":"Name","value":"completed_at"}}]}}]}}]} as unknown as DocumentNode<UpdateActionMutation, UpdateActionMutationVariables>;
export const GetAttackVectorsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetAttackVectors"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"where"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackvector_bool_exp"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}},"type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackvector_order_by"}}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"offset"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_attackvector"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}},{"kind":"Argument","name":{"kind":"Name","value":"offset"},"value":{"kind":"Variable","name":{"kind":"Name","value":"offset"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"vector_type"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"risk_score"}},{"kind":"Field","name":{"kind":"Name","value":"evidence"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}},{"kind":"Field","name":{"kind":"Name","value":"core_attackvector_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}}]}}]} as unknown as DocumentNode<GetAttackVectorsQuery, GetAttackVectorsQueryVariables>;
export const GetAttackVectorDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetAttackVector"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_attackvector_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"vector_type"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"risk_score"}},{"kind":"Field","name":{"kind":"Name","value":"evidence"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<GetAttackVectorQuery, GetAttackVectorQueryVariables>;
export const UpdateAttackVectorDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateAttackVector"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"updates"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_attackvector_set_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_attackvector_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"pk_columns"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}},{"kind":"Argument","name":{"kind":"Name","value":"_set"},"value":{"kind":"Variable","name":{"kind":"Name","value":"updates"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"vector_type"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"risk_score"}},{"kind":"Field","name":{"kind":"Name","value":"evidence"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<UpdateAttackVectorMutation, UpdateAttackVectorMutationVariables>;
export const GetMissionReviewsByOverviewDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMissionReviewsByOverview"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"overviewId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"mission_review"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"overview_id"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"Variable","name":{"kind":"Name","value":"overviewId"}}}]}}]}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"created_at"},"value":{"kind":"EnumValue","value":"desc"}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"verdict"}},{"kind":"Field","name":{"kind":"Name","value":"confidence_score"}},{"kind":"Field","name":{"kind":"Name","value":"reasoning"}},{"kind":"Field","name":{"kind":"Name","value":"rejection_reasons"}},{"kind":"Field","name":{"kind":"Name","value":"suggested_actions"}},{"kind":"Field","name":{"kind":"Name","value":"needs_human_review"}},{"kind":"Field","name":{"kind":"Name","value":"vuln_count"}},{"kind":"Field","name":{"kind":"Name","value":"confirmed_vuln_count"}},{"kind":"Field","name":{"kind":"Name","value":"high_severity_count"}},{"kind":"Field","name":{"kind":"Name","value":"has_poc_evidence"}},{"kind":"Field","name":{"kind":"Name","value":"scan_coverage_pct"}},{"kind":"Field","name":{"kind":"Name","value":"triggered_by"}},{"kind":"Field","name":{"kind":"Name","value":"triggered_by_agent"}},{"kind":"Field","name":{"kind":"Name","value":"reviewed_at"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<GetMissionReviewsByOverviewQuery, GetMissionReviewsByOverviewQueryVariables>;
export const GetMissionReviewDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMissionReview"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"mission_review_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"verdict"}},{"kind":"Field","name":{"kind":"Name","value":"confidence_score"}},{"kind":"Field","name":{"kind":"Name","value":"reasoning"}},{"kind":"Field","name":{"kind":"Name","value":"rejection_reasons"}},{"kind":"Field","name":{"kind":"Name","value":"suggested_actions"}},{"kind":"Field","name":{"kind":"Name","value":"needs_human_review"}},{"kind":"Field","name":{"kind":"Name","value":"vuln_count"}},{"kind":"Field","name":{"kind":"Name","value":"confirmed_vuln_count"}},{"kind":"Field","name":{"kind":"Name","value":"high_severity_count"}},{"kind":"Field","name":{"kind":"Name","value":"has_poc_evidence"}},{"kind":"Field","name":{"kind":"Name","value":"scan_coverage_pct"}},{"kind":"Field","name":{"kind":"Name","value":"triggered_by"}},{"kind":"Field","name":{"kind":"Name","value":"triggered_by_agent"}},{"kind":"Field","name":{"kind":"Name","value":"reviewed_at"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<GetMissionReviewQuery, GetMissionReviewQueryVariables>;
export const GetMissionReviewsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMissionReviews"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"where"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"mission_review_bool_exp"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}},"type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"mission_review_order_by"}}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"mission_review"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"verdict"}},{"kind":"Field","name":{"kind":"Name","value":"confidence_score"}},{"kind":"Field","name":{"kind":"Name","value":"reasoning"}},{"kind":"Field","name":{"kind":"Name","value":"needs_human_review"}},{"kind":"Field","name":{"kind":"Name","value":"vuln_count"}},{"kind":"Field","name":{"kind":"Name","value":"confirmed_vuln_count"}},{"kind":"Field","name":{"kind":"Name","value":"high_severity_count"}},{"kind":"Field","name":{"kind":"Name","value":"has_poc_evidence"}},{"kind":"Field","name":{"kind":"Name","value":"scan_coverage_pct"}},{"kind":"Field","name":{"kind":"Name","value":"triggered_by"}},{"kind":"Field","name":{"kind":"Name","value":"triggered_by_agent"}},{"kind":"Field","name":{"kind":"Name","value":"reviewed_at"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<GetMissionReviewsQuery, GetMissionReviewsQueryVariables>;
export const AddSeedDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"AddSeed"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"object"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_seed_insert_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"insert_core_seed_one"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"object"},"value":{"kind":"Variable","name":{"kind":"Name","value":"object"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"value"}},{"kind":"Field","name":{"kind":"Name","value":"type"}},{"kind":"Field","name":{"kind":"Name","value":"is_active"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<AddSeedMutation, AddSeedMutationVariables>;
export const DeleteSeedDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteSeed"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"delete_core_seed_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<DeleteSeedMutation, DeleteSeedMutationVariables>;
export const CreateTargetDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateTarget"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"object"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_target_insert_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"insert_core_target_one"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"object"},"value":{"kind":"Variable","name":{"kind":"Name","value":"object"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<CreateTargetMutation, CreateTargetMutationVariables>;
export const UpdateTargetDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateTarget"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"updates"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_target_set_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_target_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"pk_columns"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}},{"kind":"Argument","name":{"kind":"Name","value":"_set"},"value":{"kind":"Variable","name":{"kind":"Name","value":"updates"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<UpdateTargetMutation, UpdateTargetMutationVariables>;
export const DeleteTargetDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteTarget"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"delete_core_target_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<DeleteTargetMutation, DeleteTargetMutationVariables>;
export const GetVulnerabilitiesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVulnerabilities"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"where"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"core_vulnerability_bool_exp"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}},"type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_vulnerability_order_by"}}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"offset"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_vulnerability"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderBy"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}},{"kind":"Argument","name":{"kind":"Name","value":"offset"},"value":{"kind":"Variable","name":{"kind":"Name","value":"offset"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"ip_asset_id"}},{"kind":"Field","name":{"kind":"Name","value":"subdomain_asset_id"}},{"kind":"Field","name":{"kind":"Name","value":"url_asset_id"}},{"kind":"Field","name":{"kind":"Name","value":"source_attack_vector_id"}},{"kind":"Field","name":{"kind":"Name","value":"action_id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"cve_intelligence_id"}},{"kind":"Field","name":{"kind":"Name","value":"enrichment_status"}},{"kind":"Field","name":{"kind":"Name","value":"enrichment_attempted_at"}},{"kind":"Field","name":{"kind":"Name","value":"tool_source"}},{"kind":"Field","name":{"kind":"Name","value":"template_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"severity"}},{"kind":"Field","name":{"kind":"Name","value":"matched_at"}},{"kind":"Field","name":{"kind":"Name","value":"extracted_results"}},{"kind":"Field","name":{"kind":"Name","value":"request_raw"}},{"kind":"Field","name":{"kind":"Name","value":"response_raw"}},{"kind":"Field","name":{"kind":"Name","value":"fingerprint"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"remediation"}},{"kind":"Field","name":{"kind":"Name","value":"last_seen"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}},{"kind":"Field","name":{"kind":"Name","value":"core_target"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"core_vulnerability_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"Variable","name":{"kind":"Name","value":"where"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}}]}}]} as unknown as DocumentNode<GetVulnerabilitiesQuery, GetVulnerabilitiesQueryVariables>;
export const GetVulnerabilityDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVulnerability"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_vulnerability_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"ip_asset_id"}},{"kind":"Field","name":{"kind":"Name","value":"subdomain_asset_id"}},{"kind":"Field","name":{"kind":"Name","value":"url_asset_id"}},{"kind":"Field","name":{"kind":"Name","value":"source_attack_vector_id"}},{"kind":"Field","name":{"kind":"Name","value":"action_id"}},{"kind":"Field","name":{"kind":"Name","value":"overview_id"}},{"kind":"Field","name":{"kind":"Name","value":"cve_intelligence_id"}},{"kind":"Field","name":{"kind":"Name","value":"enrichment_status"}},{"kind":"Field","name":{"kind":"Name","value":"enrichment_attempted_at"}},{"kind":"Field","name":{"kind":"Name","value":"tool_source"}},{"kind":"Field","name":{"kind":"Name","value":"template_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"severity"}},{"kind":"Field","name":{"kind":"Name","value":"matched_at"}},{"kind":"Field","name":{"kind":"Name","value":"extracted_results"}},{"kind":"Field","name":{"kind":"Name","value":"request_raw"}},{"kind":"Field","name":{"kind":"Name","value":"response_raw"}},{"kind":"Field","name":{"kind":"Name","value":"fingerprint"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"remediation"}},{"kind":"Field","name":{"kind":"Name","value":"last_seen"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}},{"kind":"Field","name":{"kind":"Name","value":"core_target"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}}]}},{"kind":"Field","name":{"kind":"Name","value":"core_pocrecords"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"created_at"},"value":{"kind":"EnumValue","value":"desc"}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"vulnerability_id"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"content"}},{"kind":"Field","name":{"kind":"Name","value":"language"}},{"kind":"Field","name":{"kind":"Name","value":"result"}},{"kind":"Field","name":{"kind":"Name","value":"is_verified"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]}}]} as unknown as DocumentNode<GetVulnerabilityQuery, GetVulnerabilityQueryVariables>;
export const GetVulnerabilityCountsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVulnerabilityCounts"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_vulnerability_aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}},{"kind":"Field","alias":{"kind":"Name","value":"critical"},"name":{"kind":"Name","value":"core_vulnerability_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"severity"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"StringValue","value":"critical","block":false}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}},{"kind":"Field","alias":{"kind":"Name","value":"high"},"name":{"kind":"Name","value":"core_vulnerability_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"severity"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"StringValue","value":"high","block":false}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}},{"kind":"Field","alias":{"kind":"Name","value":"medium"},"name":{"kind":"Name","value":"core_vulnerability_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"severity"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"StringValue","value":"medium","block":false}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}},{"kind":"Field","alias":{"kind":"Name","value":"low"},"name":{"kind":"Name","value":"core_vulnerability_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"severity"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"StringValue","value":"low","block":false}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}},{"kind":"Field","alias":{"kind":"Name","value":"info"},"name":{"kind":"Name","value":"core_vulnerability_aggregate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"severity"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"StringValue","value":"info","block":false}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"aggregate"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}}]}}]} as unknown as DocumentNode<GetVulnerabilityCountsQuery, GetVulnerabilityCountsQueryVariables>;
export const CreateVulnerabilityDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateVulnerability"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"object"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_vulnerability_insert_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"insert_core_vulnerability_one"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"object"},"value":{"kind":"Variable","name":{"kind":"Name","value":"object"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"severity"}},{"kind":"Field","name":{"kind":"Name","value":"template_id"}},{"kind":"Field","name":{"kind":"Name","value":"matched_at"}},{"kind":"Field","name":{"kind":"Name","value":"tool_source"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"remediation"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}}]}}]}}]} as unknown as DocumentNode<CreateVulnerabilityMutation, CreateVulnerabilityMutationVariables>;
export const UpdateVulnerabilityDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateVulnerability"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"updates"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_vulnerability_set_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_vulnerability_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"pk_columns"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}},{"kind":"Argument","name":{"kind":"Name","value":"_set"},"value":{"kind":"Variable","name":{"kind":"Name","value":"updates"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"target_id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"severity"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"remediation"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<UpdateVulnerabilityMutation, UpdateVulnerabilityMutationVariables>;
export const DeleteVulnerabilityDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteVulnerability"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"delete_core_vulnerability_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<DeleteVulnerabilityMutation, DeleteVulnerabilityMutationVariables>;
export const BatchUpdateVulnerabilityStatusDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"BatchUpdateVulnerabilityStatus"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"ids"}},"type":{"kind":"NonNullType","type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"status"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_vulnerability_many"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"updates"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_in"},"value":{"kind":"Variable","name":{"kind":"Name","value":"ids"}}}]}}]}},{"kind":"ObjectField","name":{"kind":"Name","value":"_set"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"status"},"value":{"kind":"Variable","name":{"kind":"Name","value":"status"}}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"affected_rows"}}]}}]}}]} as unknown as DocumentNode<BatchUpdateVulnerabilityStatusMutation, BatchUpdateVulnerabilityStatusMutationVariables>;
export const BatchDeleteVulnerabilitiesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"BatchDeleteVulnerabilities"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"ids"}},"type":{"kind":"NonNullType","type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"delete_core_vulnerability"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_in"},"value":{"kind":"Variable","name":{"kind":"Name","value":"ids"}}}]}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"affected_rows"}}]}}]}}]} as unknown as DocumentNode<BatchDeleteVulnerabilitiesMutation, BatchDeleteVulnerabilitiesMutationVariables>;
export const GetPoCsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetPoCs"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"vulnId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"core_pocrecord"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"where"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"vulnerability_id"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"_eq"},"value":{"kind":"Variable","name":{"kind":"Name","value":"vulnId"}}}]}}]}},{"kind":"Argument","name":{"kind":"Name","value":"order_by"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"created_at"},"value":{"kind":"EnumValue","value":"desc"}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"vulnerability_id"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"content"}},{"kind":"Field","name":{"kind":"Name","value":"language"}},{"kind":"Field","name":{"kind":"Name","value":"result"}},{"kind":"Field","name":{"kind":"Name","value":"is_verified"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<GetPoCsQuery, GetPoCsQueryVariables>;
export const CreatePoCDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreatePoC"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"object"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_pocrecord_insert_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"insert_core_pocrecord_one"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"object"},"value":{"kind":"Variable","name":{"kind":"Name","value":"object"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"vulnerability_id"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"content"}},{"kind":"Field","name":{"kind":"Name","value":"language"}},{"kind":"Field","name":{"kind":"Name","value":"result"}},{"kind":"Field","name":{"kind":"Name","value":"is_verified"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<CreatePoCMutation, CreatePoCMutationVariables>;
export const UpdatePoCDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdatePoC"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"updates"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"core_pocrecord_set_input"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"update_core_pocrecord_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"pk_columns"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}},{"kind":"Argument","name":{"kind":"Name","value":"_set"},"value":{"kind":"Variable","name":{"kind":"Name","value":"updates"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"vulnerability_id"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"content"}},{"kind":"Field","name":{"kind":"Name","value":"language"}},{"kind":"Field","name":{"kind":"Name","value":"result"}},{"kind":"Field","name":{"kind":"Name","value":"is_verified"}},{"kind":"Field","name":{"kind":"Name","value":"created_at"}},{"kind":"Field","name":{"kind":"Name","value":"updated_at"}}]}}]}}]} as unknown as DocumentNode<UpdatePoCMutation, UpdatePoCMutationVariables>;
export const DeletePoCDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeletePoC"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"bigint"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"delete_core_pocrecord_by_pk"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<DeletePoCMutation, DeletePoCMutationVariables>;