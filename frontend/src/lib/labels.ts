import type { MillStatus, ShiftKey } from './types';

export const millStatusLabel: Record<MillStatus, string> = {
  grinding: '研磨中',
  idle: '待机',
  wash: '清洗',
};

// 东八区自然日三班，边界左闭右开：00:00 归夜班、08:00 归早班、16:00 归中班。
export const shiftLabel: Record<ShiftKey, string> = {
  night: '夜班',
  morning: '早班',
  afternoon: '中班',
};

export const shiftTimeRange: Record<ShiftKey, string> = {
  night: '00:00 – 08:00',
  morning: '08:00 – 16:00',
  afternoon: '16:00 – 24:00',
};

export const shiftOrder: ShiftKey[] = ['morning', 'afternoon', 'night'];
