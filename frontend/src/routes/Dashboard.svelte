<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import type { DashboardStats, ShiftSummaryResponse } from '../lib/types';

  let stats: DashboardStats | null = null;
  let shifts: ShiftSummaryResponse | null = null;
  let error = '';
  let loading = true;
  let date = '';

  async function loadShifts(selected: string) {
    const query = selected ? `?date=${encodeURIComponent(selected)}` : '';
    const res = await api<ShiftSummaryResponse>(`/dashboard/shifts${query}`);
    shifts = res;
    // 缺省查询时以后端返回的东八区日期回填输入框。
    date = res.date;
  }

  onMount(async () => {
    try {
      // 四张汇总卡与班次汇总互不依赖，并行拉取；班次数字一律来自后端接口。
      [stats, shifts] = await Promise.all([
        api<DashboardStats>('/dashboard'),
        api<ShiftSummaryResponse>('/dashboard/shifts').then((res) => {
          date = res.date;
          return res;
        }),
      ]);
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    } finally {
      loading = false;
    }
  });

  async function pickDate() {
    error = '';
    try {
      await loadShifts(date);
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    }
  }

  async function backToToday() {
    error = '';
    date = '';
    try {
      await loadShifts('');
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    }
  }
</script>

<header class="page-head">
  <h1>仪表盘</h1>
  <p>车间规模、在研机台与近 24h / 7 日台账概览</p>
</header>

{#if loading}
  <div class="muted">加载中…</div>
{:else if error}
  <div class="err">{error}</div>
{:else if stats && shifts}
  <div class="grid">
    <article>
      <div class="k">车间数</div>
      <div class="v">{stats.workshopTotal}</div>
    </article>
    <article>
      <div class="k">研磨中机台</div>
      <div class="v accent">{stats.grindingMillCount}</div>
    </article>
    <article>
      <div class="k">近 24h 粘度取样</div>
      <div class="v">{stats.samplesLast24h}</div>
    </article>
    <article>
      <div class="k">近 7 日研磨遍次</div>
      <div class="v">{stats.passesLast7d}</div>
    </article>
  </div>

  <section class="panel shift-panel">
    <div class="shift-head">
      <h2>研磨班次汇总（东八区）</h2>
      <div class="shift-filter">
        <label class="date-field">日期
          <input type="date" bind:value={date} on:change={pickDate} />
        </label>
        <button class="btn-ghost" on:click={backToToday}>今天</button>
      </div>
    </div>
    <p class="shift-note muted">
      按遍次开始时间归班：夜班 00:00–08:00、早班 08:00–16:00、午班 16:00–24:00；
      08:00 归早班，16:00 归午班，00:00 归夜班。跨午夜遍次整段计入开始时间所在班次。
    </p>
    <table class="data-table">
      <thead>
        <tr>
          <th>班次</th>
          <th>时段</th>
          <th class="num">遍次数</th>
          <th class="num">总时长（分钟）</th>
        </tr>
      </thead>
      <tbody>
        {#each shifts.shifts as s (s.key)}
          <tr>
            <td>{s.name}</td>
            <td class="muted">{s.window}</td>
            <td class="num">{s.passCount}</td>
            <td class="num">{s.totalMinutes}</td>
          </tr>
        {/each}
      </tbody>
    </table>
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

  .shift-panel {
    margin-top: 1.25rem;
  }

  .shift-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .shift-head h2 {
    margin: 0;
  }

  .shift-filter {
    display: flex;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .date-field {
    display: grid;
    gap: 0.3rem;
    font-size: 0.8rem;
    color: var(--steel);
  }

  .date-field input {
    border: 1px solid var(--line);
    background: rgba(0, 0, 0, 0.35);
    color: white;
    padding: 0.5rem 0.6rem;
  }

  .date-field input:focus {
    outline: none;
    border-color: var(--vermillion-700);
  }

  .shift-note {
    font-size: 0.82rem;
    margin: 0.6rem 0 0.9rem;
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 900px) {
    .grid {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
