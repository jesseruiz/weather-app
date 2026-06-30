import { useState, useEffect, useRef } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { Link } from 'react-router';
import { API_BASE } from './api';
import './Trivia.css';

const TIMER_MS = 15000;
const LABELS = ['A', 'B', 'C', 'D'];

export default function Trivia() {
  const { authStatus } = useAuthenticator(ctx => [ctx.authStatus]);
  const isGuest = authStatus !== 'authenticated';

  const [phase, setPhase] = useState('loading');
  // loading | error | already-played | playing | revealing | finished

  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selected, setSelected] = useState(null);  // 0-3 or null (timeout)
  const [result, setResult] = useState(null);
  const [scores, setScores] = useState([]);
  const [priorScore, setPriorScore] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(TIMER_MS);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const timeRef = useRef(TIMER_MS);
  const submittedRef = useRef(false);
  const timerRef = useRef(null);
  const dateRef = useRef('');

  const q = questions[currentIndex];

  // Wait for Amplify to finish configuring so isGuest is accurate before loading
  useEffect(() => {
    if (authStatus === 'configuring') return;
    loadQuestions();
  }, [authStatus]);

  // Timer — starts fresh each time we enter 'playing' phase or change question
  useEffect(() => {
    if (phase !== 'playing') {
      clearInterval(timerRef.current);
      return;
    }
    submittedRef.current = false;
    timeRef.current = TIMER_MS;
    setTimeRemaining(TIMER_MS);

    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      const remaining = Math.max(0, TIMER_MS - (Date.now() - startTime));
      timeRef.current = remaining;
      setTimeRemaining(remaining);
      if (remaining === 0 && !submittedRef.current) {
        submittedRef.current = true;
        clearInterval(timerRef.current);
        doSubmit(null, 0);
      }
    }, 50);

    return () => clearInterval(timerRef.current);
  }, [phase, currentIndex]);

  async function getAuthHeaders() {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      return token ? { Authorization: `Bearer ${token}` } : {};
    } catch {
      return {};
    }
  }

  async function loadQuestions() {
    setPhase('loading');
    setError('');
    try {
      const auth = await getAuthHeaders();
      const res = await fetch(`${API_BASE}/trivia/questions`, {
        headers: { ...auth, 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to load today's questions.");
        setPhase('error');
        return;
      }
      if (data.completed) {
        setPriorScore(data.totalScore ?? 0);
        setPhase('already-played');
        return;
      }
      // Guest-only: check localStorage now that we have today's date from the server
      if (isGuest) {
        try {
          const stored = JSON.parse(localStorage.getItem('trivia_played') || 'null');
          if (stored?.date === data.date) {
            setPriorScore(stored.score ?? 0);
            setPhase('already-played');
            return;
          }
        } catch { /* ignore malformed localStorage */ }
      }
      dateRef.current = data.date;
      setQuestions(data.questions);
      setCurrentIndex(0);
      setScores([]);
      setSelected(null);
      setResult(null);
      setPhase('playing');
    } catch {
      setError('Network error. Please check your connection and try again.');
      setPhase('error');
    }
  }

  async function handleChoice(i) {
    if (submittedRef.current || selected !== null || submitting) return;
    submittedRef.current = true;
    clearInterval(timerRef.current);
    setSelected(i);
    await doSubmit(i, timeRef.current);
  }

  async function doSubmit(choiceIndex, timeRemainingMs) {
    setSubmitting(true);
    try {
      const auth = await getAuthHeaders();
      const res = await fetch(`${API_BASE}/trivia/submit`, {
        method: 'POST',
        headers: { ...auth, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questionId: q.questionId,
          answer: choiceIndex ?? 0,
          timeRemainingMs: Math.round(timeRemainingMs),
        }),
      });
      const data = await res.json();
      if (choiceIndex === null) {
        // Timed out — force 0 points regardless of answer sent
        setResult({ ...data, correct: false, pointsEarned: 0 });
      } else if (res.ok) {
        setResult(data);
      } else {
        setResult({ correct: false, correctAnswer: 0, explanation: '', pointsEarned: 0 });
      }
    } catch {
      setResult({ correct: false, correctAnswer: 0, explanation: 'Could not reach server.', pointsEarned: 0 });
    }
    setSubmitting(false);
    setPhase('revealing');
  }

  function handleNext() {
    const newScores = [...scores, result?.pointsEarned ?? 0];
    if (currentIndex + 1 >= questions.length) {
      setScores(newScores);
      // Lock anonymous users out for the rest of the day via localStorage
      if (isGuest) {
        const total = newScores.reduce((a, b) => a + b, 0);
        try {
          localStorage.setItem('trivia_played', JSON.stringify({ date: dateRef.current, score: total }));
        } catch { /* ignore quota errors */ }
      }
      setPhase('finished');
    } else {
      setScores(newScores);
      setCurrentIndex(i => i + 1);
      setSelected(null);
      setResult(null);
      setPhase('playing');
    }
  }

  // --- Screens ---

  if (phase === 'loading') return (
    <div className="trivia-page">
      <div className="trivia-card trivia-center">
        <div className="trivia-spinner" />
        <p className="trivia-muted">Loading today's questions…</p>
      </div>
    </div>
  );

  if (phase === 'error') return (
    <div className="trivia-page">
      <div className="trivia-card trivia-center">
        <h2>Something went wrong</h2>
        <p className="trivia-muted">{error}</p>
        <button className="trivia-btn" onClick={loadQuestions}>Try Again</button>
      </div>
    </div>
  );

  if (phase === 'already-played') return (
    <div className="trivia-page">
      <div className="trivia-card trivia-center">
        <div className="trivia-emoji" aria-hidden="true">🏆</div>
        <h2>You've already played today</h2>
        <p className="trivia-big-score">{priorScore} <span>pts</span></p>
        <p className="trivia-muted">
          New questions drop at midnight Pacific time.<br />Check back tomorrow!
        </p>
      </div>
    </div>
  );

  if (phase === 'finished') {
    const total = scores.reduce((a, b) => a + b, 0);
    return (
      <div className="trivia-page">
        <div className="trivia-card trivia-center">
          <div className="trivia-emoji" aria-hidden="true">🎉</div>
          <h2>That's a wrap!</h2>
          <p className="trivia-big-score">{total} <span>pts</span></p>
          <div className="trivia-breakdown">
            {scores.map((s, i) => (
              <div key={i} className={`trivia-breakdown-row ${s > 0 ? 'hit' : 'miss'}`}>
                <span>Q{i + 1}</span>
                <span>{s > 0 ? `+${s}` : '—'}</span>
              </div>
            ))}
          </div>
          <p className="trivia-muted">
            New questions drop at midnight Pacific time.<br />Check back tomorrow!
          </p>
        </div>
      </div>
    );
  }

  // playing or revealing
  const isRevealing = phase === 'revealing';
  const timedOut = selected === null && isRevealing;
  const timerPct = (timeRemaining / TIMER_MS) * 100;

  return (
    <div className="trivia-page">
      {isGuest && (
        <div className="trivia-guest-banner">
          <Link to="/login">Sign in</Link> to save your score and appear on the leaderboard.
        </div>
      )}
      <div className="trivia-topbar">
        <h1>Daily Weather Trivia</h1>
        <span className="trivia-dots">
          {questions.map((_, i) => (
            <span
              key={i}
              className={`trivia-dot ${i < currentIndex ? 'done' : i === currentIndex ? 'active' : ''}`}
            />
          ))}
        </span>
      </div>

      <div className="trivia-card">
        <div className="trivia-timer-track">
          {!isRevealing && (
            <div
              className={`trivia-timer-fill ${timeRemaining < 5000 ? 'low' : ''}`}
              style={{ width: `${timerPct}%` }}
            />
          )}
        </div>

        <div className="trivia-body">
          <div className="trivia-meta">
            <span className="trivia-badge">{q?.category}</span>
            {!isRevealing && (
              <span className="trivia-timer-text">{Math.ceil(timeRemaining / 1000)}s</span>
            )}
          </div>

          <p className="trivia-question">{q?.question}</p>

          <div className="trivia-choices">
            {q?.choices.map((choice, i) => {
              let cls = 'trivia-choice';
              if (isRevealing) {
                if (i === result?.correctAnswer) cls += ' correct';
                else if (i === selected) cls += ' wrong';
                else cls += ' dimmed';
              }
              return (
                <button
                  key={i}
                  className={cls}
                  onClick={() => handleChoice(i)}
                  disabled={isRevealing || submitting}
                >
                  <span className="trivia-label">{LABELS[i]}</span>
                  <span>{choice}</span>
                </button>
              );
            })}
          </div>

          {isRevealing && (
            <div className="trivia-reveal" aria-live="polite" aria-atomic="true">
              <div className={`trivia-feedback ${result?.correct && !timedOut ? 'correct' : 'wrong'}`}>
                {timedOut
                  ? "⏰ Time's up! +0 pts"
                  : result?.correct
                  ? `✓ Correct! +${result.pointsEarned} pts`
                  : `✗ Incorrect — +0 pts`}
              </div>
              {result?.explanation && (
                <p className="trivia-explanation">{result.explanation}</p>
              )}
              <button className="trivia-btn trivia-next" onClick={handleNext}>
                {currentIndex + 1 >= questions.length ? 'See Results' : 'Next Question →'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
