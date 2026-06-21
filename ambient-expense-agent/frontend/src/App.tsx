import { useEffect, useState } from 'react';
import './index.css';

interface ExpenseRun {
  run_id: string;
  status: string;
  state: {
    prompt: string;
    clean_description: string;
    security_flag: boolean;
    llm_routing: string;
    human_review_status: string;
    final_recorded: boolean;
    llm_review_result?: string;
  };
}

function App() {
  const [runs, setRuns] = useState<ExpenseRun[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = async () => {
    try {
      // Fetch runs from ADK server
      const response = await fetch('http://localhost:8080/apps/expense_agent/runs');
      if (response.ok) {
        const data = await response.json();
        // data might be { runs: [] } or just an array
        const runsArray = Array.isArray(data) ? data : data.runs || [];
        setRuns(runsArray);
      }
    } catch (error) {
      console.error('Failed to fetch runs', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (runId: string, decision: string) => {
    try {
      await fetch(`http://localhost:8080/apps/expense_agent/runs/${runId}/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          state: { human_review_status: decision }
        })
      });
      fetchRuns();
    } catch (error) {
      console.error('Failed to resume run', error);
    }
  };

  // Filter for runs pending human review
  const pendingRuns = runs.filter(
    (run) => run.state?.human_review_status === 'pending review' && !run.state?.final_recorded
  );

  return (
    <div className="app-container">
      <header className="glass-header">
        <h1>Ambient Expense Agent</h1>
        <span className="badge">{pendingRuns.length} Pending Approvals</span>
      </header>

      <main className="content">
        {loading ? (
          <div className="loader">Loading...</div>
        ) : pendingRuns.length === 0 ? (
          <div className="empty-state">
            <h2>You're all caught up!</h2>
            <p>No expenses require human review at this time.</p>
          </div>
        ) : (
          <div className="card-grid">
            {pendingRuns.map((run) => (
              <div key={run.run_id} className="glass-card">
                <div className="card-header">
                  <span className="id-badge">ID: {run.run_id.substring(0, 8)}</span>
                  {run.state.security_flag && (
                    <span className="warning-badge">⚠️ Security Flag</span>
                  )}
                </div>
                
                <div className="card-body">
                  <h3>Expense Description</h3>
                  <p className="description">{run.state.clean_description}</p>
                  
                  {run.state.llm_review_result && (
                    <div className="llm-insight">
                      <strong>AI Review:</strong> {run.state.llm_review_result}
                    </div>
                  )}
                </div>

                <div className="card-actions">
                  <button 
                    onClick={() => handleDecision(run.run_id, 'approved')}
                    className="btn btn-approve"
                  >
                    Approve
                  </button>
                  <button 
                    onClick={() => handleDecision(run.run_id, 'rejected')}
                    className="btn btn-reject"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
