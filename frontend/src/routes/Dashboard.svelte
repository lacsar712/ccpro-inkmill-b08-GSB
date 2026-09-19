<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import { shiftLabel, shiftOrder, shiftTimeRange } from '../lib/labels';
  import type { DashboardStats, DashboardShifts } from '../lib/types';

  let data: DashboardStats | null = null;
  let shifts: DashboardShifts | null = null;
  let error = '';
  let shiftError = '';
  let loading = true;
  let shiftLoading = false;
  let selectedDate = todayInCst();

  // 东八区（UTC+8）自然日的今天，不用浏览器本地时区或 UTC 零点。
  function todayInCst(): string {
    const cst = new Date(Date.now() + 8 * 60 * 60 * 1000);
    return cst.toISOString().slice(0, 10);
  }

  function formatMinutes(value: number): string {
    return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/\.?0+$/, '');
  }

  async function loadShifts(date: string) {
    shiftLoading = true;
    shiftError = '';
    try {
      shifts = await api<DashboardShifts>(`/dashboard/shifts?date=${encodeURIComponent(date)}`);
    } catch (e) {
      shiftError = e instanceof Error ? e.message : '班次汇总加载失败';
    } finally {
      shiftLoading = false;
    }
  }

  function onDateChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    if (!value) return;
    selectedDate = value;
    loadShifts(value);
  }

  function resetToday() {
    selectedDate = todayInCst();
    loadShifts(selectedDate);
  }

  onMount(async () => {
    try {
      data = await api<DashboardStats>('/dashboard');
      await loadShifts(selectedDate);
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    } finally {
      loading = false;
    }
  });
</script>

<header class="page-head">
  <h1>仪表盘</h1>
  <p>车间规模、在研机台与近 24h / 7 日台账概览</p>
</header>

{#if loading}
  <div class="muted">加载中…</div>
{:else if error}
  <div class="err">{error}</div>
{:else if data}
  <div class="grid">
    <article>
      <div class="k">车间数</div>
      <div class="v">{data.workshopTotal}</div>
    </article>
    <article>
      <div class="k">研磨中机台</div>
      <div class="v accent">{data.grindingMillCount}</div>
    </article>
    <article>
      <div class="k">近 24h 粘度取样</div>
      <div class="v">{data.samplesLast24h}</div>
    </article>
    <article>
      <div class="k">近 7 日研磨遍次</div>
      <div class="v">{data.passesLast7d}</div>
    </article>
  </div>

  <section class="shifts">
    <div class="shifts-head">
      <h2>研磨班次汇总</h2>
      <div class="date-picker">
        <label for="shift-date">日期（东八区）</label>
        <input id="shift-date" type="date" value={selectedDate} on:change={onDateChange} />
        <button type="button" class="today-btn" on:click={resetToday}>今天</button>
      </div>
    </div>
    <p class="hint">
      按遍次开始时间归班：早班 08:00–16:00、中班 16:00–24:00、夜班 00:00–08:00；
      08:00 归早班、16:00 归中班、00:00 归夜班；跨午夜遍次整段计入开始班次，不拆分。
    </p>

    {#if shiftLoading}
      <div class="muted">班次汇总加载中…</div>
    {:else if shiftError}
      <div class="err">{shiftError}</div>
    {:else if shifts}
      <table>
        <thead>
          <tr>
            <th>班次</th>
            <th>时段（东八区）</th>
            <th class="num">遍次数</th>
            <th class="num">总时长（分钟）</th>
          </tr>
        </thead>
        <tbody>
          {#each shiftOrder as key}
            <tr>
              <td>{shiftLabel[key]}</td>
              <td class="muted">{shiftTimeRange[key]}</td>
              <td class="num">{shifts.shifts[key].passCount}</td>
              <td class="num">{formatMinutes(shifts.shifts[key].totalMinutes)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
{/if}

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
  }

  article {
    padding: 1.2rem 1.1rem;
    background: rgba(18, 18, 18, 0.85);
    border: 1px solid var(--line);
    border-top: 3px solid var(--ink-700);
  }

  article:nth-child(2) {
    border-top-color: var(--vermillion-700);
  }

  article:nth-child(3) {
    border-top-color: var(--paper);
  }

  .k {
    color: var(--steel);
    font-size: 0.85rem;
  }

  .v {
    margin-top: 0.55rem;
    font-family: var(--font-display);
    font-size: 2.4rem;
    letter-spacing: 0.04em;
  }

  .accent {
    color: var(--vermillion-400);
  }

  .shifts {
    margin-top: 2rem;
    padding: 1.2rem 1.1rem;
    background: rgba(18, 18, 18, 0.85);
    border: 1px solid var(--line);
  }

  .shifts-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .shifts-head h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.3rem;
  }

  .date-picker {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  .date-picker label {
    color: var(--steel);
    font-size: 0.85rem;
  }

  .date-picker input {
    background: #141414;
    color: var(--paper);
    border: 1px solid var(--line);
    padding: 0.35rem 0.5rem;
    color-scheme: dark;
  }

  .today-btn {
    background: transparent;
    color: var(--paper);
    border: 1px solid var(--vermillion-700);
    padding: 0.35rem 0.8rem;
    cursor: pointer;
  }

  .today-btn:hover {
    background: rgba(255, 255, 255, 0.06);
  }

  .hint {
    margin: 0.6rem 0 1rem;
    color: var(--steel);
    font-size: 0.82rem;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th,
  td {
    text-align: left;
    padding: 0.6rem 0.7rem;
    border-bottom: 1px solid var(--line);
  }

  th {
    color: var(--steel);
    font-weight: 600;
    font-size: 0.85rem;
  }

  td.num,
  th.num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 900px) {
    .grid {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
