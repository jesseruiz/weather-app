import { useState, useEffect } from 'react';
import { API_BASE } from './api';
import './Leaderboard.css';

const PERIODS = ['daily', 'weekly', 'monthly', 'yearly'];
const PERIOD_LABELS = { daily: 'Today', weekly: 'This Week', monthly: 'This Month', yearly: 'This Year' };
const TROPHIES = ['🥇', '🥈', '🥉'];

export default function Leaderboard() {
  const [boards, setBoards] = useState({ daily: null, weekly: null, monthly: null, yearly: null });

  useEffect(() => {
    Promise.all(
      PERIODS.map(p =>
        fetch(`${API_BASE}/trivia/leaderboard?period=${p}`)
          .then(r => r.json())
          .then(data => ({ period: p, entries: data.leaderboard || [] }))
          .catch(() => ({ period: p, entries: [] }))
      )
    ).then(results => {
      const next = {};
      results.forEach(({ period, entries }) => { next[period] = entries; });
      setBoards(next);
    });
  }, []);

  return (
    <div className="lb-page">
      <h1 className="lb-title">Trivia Leaderboards</h1>
      <div className="lb-grid">
        {PERIODS.map(period => (
          <div key={period} className="lb-board">
            <h2 className="lb-board-title">{PERIOD_LABELS[period]}</h2>
            {boards[period] === null ? (
              <p className="lb-loading">Loading…</p>
            ) : boards[period].length === 0 ? (
              <p className="lb-empty">No scores yet</p>
            ) : (
              <ol className="lb-list">
                {boards[period].map(entry => (
                  <li key={entry.userId} className={`lb-row ${entry.rank <= 3 ? 'lb-row-top' : ''}`}>
                    <span className="lb-rank">
                      {entry.rank <= 3
                        ? <span aria-label={`Rank ${entry.rank}`}>{TROPHIES[entry.rank - 1]}</span>
                        : <span className="lb-rank-num">{entry.rank}</span>}
                    </span>
                    <span className="lb-name">{entry.displayName}</span>
                    <span className="lb-score">{entry.score}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
