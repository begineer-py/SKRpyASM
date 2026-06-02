import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const schedulerApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/scheduler`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

export interface IntervalSchedule {
  id: number;
  every: number;
  period: string;
}

export interface CrontabSchedule {
  id: number;
  minute: string;
  hour: string;
  day_of_week: string;
  day_of_month: string;
  month_of_year: string;
  timezone: string | null;
}

export interface PeriodicTask {
  id: number;
  name: string;
  task: string;
  task_doc: string | null;
  enabled: boolean;
  description: string;
  interval: IntervalSchedule | null;
  crontab: CrontabSchedule | null;
  args: string;
  kwargs: string;
  queue: string | null;
  one_off: boolean;
  last_run_at: string | null;
  total_run_count: number;
  date_changed: string;
}

export interface RegisteredTask {
  name: string;
  doc: string | null;
}

export interface CreateTaskPayload {
  name: string;
  task: string;
  description?: string;
  enabled?: boolean;
  interval: { every: number; period: string };
  args?: string;
  kwargs?: string;
}

export interface UpdateTaskPayload {
  name?: string;
  task?: string;
  description?: string;
  enabled?: boolean;
  interval?: { every: number; period: string };
  crontab?: {
    minute?: string;
    hour?: string;
    day_of_week?: string;
    day_of_month?: string;
    month_of_year?: string;
  };
  args?: string;
  kwargs?: string;
}

export const SchedulerService = {
  listTasks: async (): Promise<PeriodicTask[]> => {
    const res = await schedulerApi.get<PeriodicTask[]>('/tasks');
    return res.data;
  },

  createTask: async (payload: CreateTaskPayload): Promise<PeriodicTask> => {
    const res = await schedulerApi.post<PeriodicTask>('/tasks', payload);
    return res.data;
  },

  updateTask: async (taskId: number, payload: UpdateTaskPayload): Promise<PeriodicTask> => {
    const res = await schedulerApi.put<PeriodicTask>(`/tasks/${taskId}`, payload);
    return res.data;
  },

  deleteTask: async (taskId: number): Promise<void> => {
    await schedulerApi.delete(`/tasks/${taskId}`);
  },

  listIntervals: async (): Promise<IntervalSchedule[]> => {
    const res = await schedulerApi.get<IntervalSchedule[]>('/schedules/intervals');
    return res.data;
  },

  listRegisteredTasks: async (): Promise<RegisteredTask[]> => {
    const res = await schedulerApi.get<RegisteredTask[]>('/registered_tasks');
    return res.data;
  },
};
