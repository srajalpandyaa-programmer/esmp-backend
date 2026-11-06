import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

type User = { id: string; full_name: string; email: string; role: string }
type Ticket = {
  id: string
  ticket_number: string
  title: string
  category: string
  priority: string
  status: string
  created_at: string
}
type Dashboard = {
  tickets_total: number
  tickets_open: number
  approvals_pending: number
  notifications_unread: number
}
type Section = 'Overview' | 'Tickets' | 'Assets' | 'Approvals' | 'Notifications'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [section, setSection] = useState<Section>('Overview')
  const [error, setError] = useState('')

  useEffect(() => {
    if (localStorage.getItem('access_token')) {
      request<User>('/auth/me').then(setUser).catch(() => localStorage.clear())
    }
  }, [])

  if (!user) {
    return <Login onLogin={(nextUser) => setUser(nextUser)} />
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">E</span><span>ESMP</span></div>
        <p className="workspace-label">WORKSPACE</p>
        <nav>
          {(['Overview', 'Tickets', 'Assets', 'Approvals', 'Notifications'] as Section[]).map((item) => (
            <button className={section === item ? 'nav-item active' : 'nav-item'} key={item} onClick={() => setSection(item)}>
              <span className="nav-icon">{({ Overview: '⌂', Tickets: '◈', Assets: '▣', Approvals: '✓', Notifications: '◌' } as Record<Section, string>)[item]}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-mini"><span className="avatar">{user.full_name[0]}</span><div><strong>{user.full_name}</strong><small>{user.role}</small></div></div>
          <button className="signout" onClick={() => { localStorage.clear(); setUser(null) }}>↪ Sign out</button>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <b>{section}</b></div><div className="top-actions"><span className="status-dot">●</span> System operational <button className="bell" onClick={() => setSection('Notifications')}>♧</button></div></header>
        {error && <div className="error-banner">{error}<button onClick={() => setError('')}>×</button></div>}
        <section className="page-content">
          {section === 'Overview' && <Overview onError={setError} onNavigate={setSection} />}
          {section === 'Tickets' && <Tickets onError={setError} />}
          {section === 'Assets' && <SimpleList title="Asset inventory" endpoint="/assets" columns={['asset_code', 'asset_type', 'status', 'assigned_to']} onError={setError} />}
          {section === 'Approvals' && <SimpleList title="Approval requests" endpoint="/approvals" columns={['request_type', 'status', 'description']} onError={setError} />}
          {section === 'Notifications' && <Notifications onError={setError} />}
        </section>
      </main>
    </div>
  )
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [employeeCode, setEmployeeCode] = useState('')
  const [error, setError] = useState('')
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    try {
      const path = mode === 'login' ? '/auth/login' : '/auth/register'
      const body = mode === 'login' ? { email, password } : { email, password, full_name: name, employee_code: employeeCode }
      const result = await request<{ access_token?: string; user?: User }>(path, { method: 'POST', body: JSON.stringify(body) })
      if (mode === 'register') {
        setMode('login'); setError('Account created. Sign in to continue.'); return
      }
      localStorage.setItem('access_token', result.access_token!)
      onLogin(result.user!)
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to sign in') }
  }
  return <div className="login-page"><div className="login-art"><div className="art-glow" /><div className="brand large"><span className="brand-mark">E</span><span>ESMP</span></div><h1>Service operations,<br /><em>made simple.</em></h1><p>One workspace for every request, asset and approval across your organization.</p><div className="quote">“The clearest path from issue to resolution.”</div></div><div className="login-panel"><div className="mobile-brand brand"><span className="brand-mark">E</span> ESMP</div><div className="form-wrap"><span className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'GET STARTED'}</span><h2>{mode === 'login' ? 'Sign in to your workspace' : 'Create your account'}</h2><p className="muted">{mode === 'login' ? 'Enter your credentials to continue.' : 'Public accounts start with Employee access.'}</p><form onSubmit={submit}>{mode === 'register' && <><label>Full name<input value={name} onChange={(e) => setName(e.target.value)} required /></label><label>Employee code<input value={employeeCode} onChange={(e) => setEmployeeCode(e.target.value)} required /></label></>}<label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required /></label>{error && <div className="form-message">{error}</div>}<button className="primary full" type="submit">{mode === 'login' ? 'Sign in  →' : 'Create account  →'}</button></form><button className="switch" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Need an account? Create one' : 'Already have an account? Sign in'}</button></div></div></div>
}

function Overview({ onError, onNavigate }: { onError: (message: string) => void; onNavigate: (section: Section) => void }) {
  const [data, setData] = useState<Dashboard>({ tickets_total: 0, tickets_open: 0, approvals_pending: 0, notifications_unread: 0 })
  const [tickets, setTickets] = useState<Ticket[]>([])
  useEffect(() => { Promise.all([request<Dashboard>('/dashboard/me'), request<Ticket[]>('/tickets?limit=5')]).then(([summary, recent]) => { setData(summary); setTickets(recent) }).catch((e) => onError(e.message)) }, [onError])
  return <><div className="welcome"><div><span className="eyebrow">OVERVIEW</span><h1>Good morning, <em>let's get things done.</em></h1><p>Here’s what’s happening across your service workspace today.</p></div><button className="primary" onClick={() => onNavigate('Tickets')}>＋ New ticket</button></div><div className="stat-grid"><Stat label="Total tickets" value={data.tickets_total} trend="All time" icon="◈" /><Stat label="Open tickets" value={data.tickets_open} trend="Needs attention" icon="◉" accent /><Stat label="Pending approvals" value={data.approvals_pending} trend="Awaiting review" icon="✓" /><Stat label="Unread notifications" value={data.notifications_unread} trend="Keep up to date" icon="◌" /></div><div className="content-grid"><div className="card"><div className="card-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h3>Your recent tickets</h3></div><button className="text-button" onClick={() => onNavigate('Tickets')}>View all →</button></div>{tickets.length === 0 ? <Empty text="No tickets yet. Create your first request." /> : tickets.map((ticket) => <TicketRow key={ticket.id} ticket={ticket} />)}</div><div className="card quick-card"><span className="eyebrow">QUICK ACTIONS</span><h3>What would you like to do?</h3><button onClick={() => onNavigate('Tickets')}>◈ <span><b>Submit a ticket</b><small>Report an issue or request help</small></span> →</button><button onClick={() => onNavigate('Assets')}>▣ <span><b>View my assets</b><small>See assigned equipment</small></span> →</button><button onClick={() => onNavigate('Approvals')}>✓ <span><b>Check approvals</b><small>Review pending requests</small></span> →</button></div></div></>
}

function Tickets({ onError }: { onError: (message: string) => void }) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState(''); const [description, setDescription] = useState(''); const [priority, setPriority] = useState('Medium')
  const load = () => request<Ticket[]>('/tickets?limit=100').then(setTickets).catch((e) => onError(e.message))
  useEffect(() => { void load() }, [])
  const create = async (event: FormEvent) => { event.preventDefault(); try { await request('/tickets', { method: 'POST', body: JSON.stringify({ title, description, category: 'General', priority }) }); setTitle(''); setDescription(''); setShowForm(false); load() } catch (e) { onError(e instanceof Error ? e.message : 'Unable to create ticket') } }
  return <><div className="page-heading"><div><span className="eyebrow">SERVICE DESK</span><h1>Tickets</h1><p>Track issues and requests from start to resolution.</p></div><button className="primary" onClick={() => setShowForm(!showForm)}>＋ New ticket</button></div>{showForm && <form className="card ticket-form" onSubmit={create}><label>Title<input value={title} onChange={(e) => setTitle(e.target.value)} required /></label><label>Description<textarea value={description} onChange={(e) => setDescription(e.target.value)} required /></label><label>Priority<select value={priority} onChange={(e) => setPriority(e.target.value)}><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></label><button className="primary" type="submit">Submit ticket</button></form>}<div className="card table-card"><div className="table-toolbar"><h3>All tickets <span className="count">{tickets.length}</span></h3><span className="muted">Most recent first</span></div>{tickets.length ? <div className="table-wrap"><table><thead><tr><th>Ticket</th><th>Title</th><th>Priority</th><th>Status</th><th>Created</th></tr></thead><tbody>{tickets.map((t) => <tr key={t.id}><td className="mono">{t.ticket_number}</td><td><b>{t.title}</b><small>{t.category}</small></td><td><span className={`priority ${t.priority.toLowerCase()}`}>{t.priority}</span></td><td><span className="badge">{t.status}</span></td><td className="muted">{new Date(t.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div> : <Empty text="No tickets found." />}</div></>
}

function SimpleList({ title, endpoint, columns, onError }: { title: string; endpoint: string; columns: string[]; onError: (message: string) => void }) {
  const [items, setItems] = useState<Record<string, string>[]>([])
  useEffect(() => { request<Record<string, string>[]>(endpoint).then(setItems).catch((e) => onError(e.message)) }, [endpoint, onError])
  return <><div className="page-heading"><div><span className="eyebrow">WORKSPACE</span><h1>{title}</h1><p>Manage and review your organization’s records.</p></div></div><div className="card table-card"><div className="table-wrap"><table><thead><tr>{columns.map((column) => <th key={column}>{column.replace('_', ' ')}</th>)}</tr></thead><tbody>{items.map((item, index) => <tr key={item.id ?? index}>{columns.map((column) => <td key={column}>{item[column] || '—'}</td>)}</tr>)}</tbody></table></div>{!items.length && <Empty text="Nothing to show yet." />}</div></>
}

function Notifications({ onError }: { onError: (message: string) => void }) {
  const [items, setItems] = useState<Record<string, string | boolean>[]>([])
  useEffect(() => {
    request<Record<string, string | boolean>[]>('/notifications').then(setItems).catch((e) => onError(e.message))
  }, [onError])
  const markAllRead = () => {
    request('/notifications/read-all', { method: 'PATCH' }).then(() => {
      setItems(items.map((item) => ({ ...item, is_read: true })))
    }).catch((e) => onError(e.message))
  }
  return <><div className="page-heading"><div><span className="eyebrow">INBOX</span><h1>Notifications</h1><p>Stay informed about your requests and approvals.</p></div><button className="secondary" onClick={markAllRead}>Mark all read</button></div><div className="card notification-list">{items.length ? items.map((item, i) => <div className={item.is_read ? 'notification read' : 'notification'} key={String(item.id ?? i)}><span className="notification-dot" /><div><b>{String(item.title)}</b><p>{String(item.message)}</p><small>{String(item.created_at)}</small></div></div>) : <Empty text="You’re all caught up." />}</div></>
}
function Stat({ label, value, trend, icon, accent = false }: { label: string; value: number; trend: string; icon: string; accent?: boolean }) { return <div className={accent ? 'stat accent' : 'stat'}><div className="stat-top"><span>{label}</span><i>{icon}</i></div><strong>{value}</strong><small>{trend}</small></div> }
function TicketRow({ ticket }: { ticket: Ticket }) { return <div className="ticket-row"><div className="ticket-symbol">◈</div><div><b>{ticket.title}</b><small>{ticket.ticket_number} · {new Date(ticket.created_at).toLocaleDateString()}</small></div><span className="badge">{ticket.status}</span></div> }
function Empty({ text }: { text: string }) { return <div className="empty">{text}</div> }

export default App
