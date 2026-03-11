import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { api, notificationApi } from '../api/api';
import { Loader } from '../components/Loader';
import { ComplaintStatusBadge, PriorityBadge } from '../components/Badges';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Bell, Search, Filter, FileText, AlertCircle, CheckCircle2, TrendingUp, Zap } from 'lucide-react';
import { useNotificationStore } from '../hooks/useNotifications';
import { toast } from 'sonner';

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

export const AdminDashboard = () => {
    const { isConnected } = useNotificationStore();
    const [complaints, setComplaints] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterDept, setFilterDept] = useState('ALL');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [filterPriority, setFilterPriority] = useState('ALL');

    // Notification form
    const [showNotifForm, setShowNotifForm] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [notifForm, setNotifForm] = useState({
        recipient_email: '',
        subject: '',
        message: '',
        notification_type: 'SYSTEM'
    });

    useEffect(() => {
        const fetchAllComplaints = async () => {
            try {
                const res = await api.get('/admin/complaints/all');
                setComplaints(res.data);
            } catch (error) {
                console.error('Failed to fetch all complaints', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAllComplaints();
    }, []);

    const handleSendNotification = async (e) => {
        e.preventDefault();
        setIsSending(true);
        try {
            await notificationApi.post('/send-notification', notifForm);
            toast.success('Notification sent successfully');
            setNotifForm({ recipient_email: '', subject: '', message: '', notification_type: 'SYSTEM' });
            setShowNotifForm(false);
        } catch (error) {
            toast.error('Failed to send notification');
        } finally {
            setIsSending(false);
        }
    };

    // Derived data
    const departments = useMemo(() => [...new Set(complaints.map(c => c.department).filter(Boolean))], [complaints]);
    const categories = useMemo(() => [...new Set(complaints.map(c => c.category).filter(Boolean))], [complaints]);

    const stats = useMemo(() => ({
        total: complaints.length,
        pending: complaints.filter(c => !['RESOLVED', 'CLOSED', 'DUMPED'].includes(c.status)).length,
        resolved: complaints.filter(c => c.status === 'RESOLVED').length,
        closed: complaints.filter(c => c.status === 'CLOSED').length,
        dumped: complaints.filter(c => c.status === 'DUMPED').length,
        departments: departments.length,
    }), [complaints, departments]);

    const categoryData = useMemo(() => {
        const counts = {};
        complaints.forEach(c => {
            const cat = c.category || 'Unknown';
            counts[cat] = (counts[cat] || 0) + 1;
        });
        return Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
    }, [complaints]);

    const statusPieData = useMemo(() => {
        const counts = {};
        complaints.forEach(c => {
            counts[c.status] = (counts[c.status] || 0) + 1;
        });
        return Object.entries(counts).map(([name, value]) => ({ name: name.replace('_', ' '), value }));
    }, [complaints]);

    const deptData = useMemo(() => {
        const counts = {};
        complaints.forEach(c => {
            const d = c.department || 'Unknown';
            counts[d] = (counts[d] || 0) + 1;
        });
        return Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
    }, [complaints]);

    const filteredComplaints = useMemo(() => {
        return complaints.filter(c => {
            const matchesSearch = searchTerm === '' ||
                c.complaint_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (c.department || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                (c.category || '').toLowerCase().includes(searchTerm.toLowerCase());
            const matchesDept = filterDept === 'ALL' || c.department === filterDept;
            const matchesStatus = filterStatus === 'ALL' || c.status === filterStatus;
            const matchesPriority = filterPriority === 'ALL' || c.priority === filterPriority;
            return matchesSearch && matchesDept && matchesStatus && matchesPriority;
        });
    }, [complaints, searchTerm, filterDept, filterStatus, filterPriority]);

    if (isLoading) return <Loader size="lg" className="h-64" />;

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">System Overview</h1>
                    <p className="text-gray-500 mt-1">All complaints across departments</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-1 bg-white border border-gray-100 rounded-full shadow-sm">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">{isConnected ? 'Live' : 'Offline'}</span>
                    </div>
                    <button
                        onClick={() => setShowNotifForm(!showNotifForm)}
                        className="px-5 py-2.5 bg-gray-900 text-white font-medium rounded-xl hover:bg-black transition-colors flex items-center gap-2 shadow-lg shadow-gray-200"
                    >
                        <Bell className="w-4 h-4" /> Send Notification
                    </button>
                </div>
            </div>

            {/* Notification Form Modal */}
            {showNotifForm && (
                <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-200 animate-in fade-in duration-200">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Manual Notification</h3>
                    <form onSubmit={handleSendNotification} className="grid sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Recipient Email</label>
                            <input type="email" required className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm" value={notifForm.recipient_email} onChange={e => setNotifForm({ ...notifForm, recipient_email: e.target.value })} />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                            <input type="text" required className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm" value={notifForm.subject} onChange={e => setNotifForm({ ...notifForm, subject: e.target.value })} />
                        </div>
                        <div className="sm:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                            <textarea required rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm" value={notifForm.message} onChange={e => setNotifForm({ ...notifForm, message: e.target.value })} />
                        </div>
                        <div className="sm:col-span-2 flex justify-end gap-3">
                            <button type="button" onClick={() => setShowNotifForm(false)} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition text-sm font-medium">Cancel</button>
                            <button type="submit" disabled={isSending} className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition text-sm">{isSending ? 'Sending...' : 'Send'}</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
                {[
                    { label: 'Total', value: stats.total, icon: FileText, color: 'text-blue-600', bg: 'bg-blue-100' },
                    { label: 'Active', value: stats.pending, icon: AlertCircle, color: 'text-orange-600', bg: 'bg-orange-100' },
                    { label: 'Resolved', value: stats.resolved, icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-100' },
                    { label: 'Closed', value: stats.closed, icon: Zap, color: 'text-gray-600', bg: 'bg-gray-100' },
                    { label: 'Dumped', value: stats.dumped, icon: Filter, color: 'text-red-600', bg: 'bg-red-100' },
                    { label: 'Depts', value: stats.departments, icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-100' },
                ].map(stat => (
                    <div key={stat.label} className="bg-white rounded-2xl border border-gray-100 p-5 flex items-center justify-between shadow-sm">
                        <div className="min-w-0">
                            <p className="text-xs font-bold text-gray-500 truncate uppercase tracking-tight">{stat.label}</p>
                            <p className="mt-1 text-2xl font-black text-gray-900">{stat.value}</p>
                        </div>
                        <div className={`p-2.5 rounded-xl ${stat.bg} flex-shrink-0`}>
                            <stat.icon className={`w-5 h-5 ${stat.color}`} />
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">By Category</h3>
                    <div className="h-72 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={categoryData} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis 
                                    dataKey="name" 
                                    tick={{ fontSize: 10, fill: '#64748b', fontWeight: 600 }} 
                                    tickLine={false} 
                                    axisLine={false} 
                                    interval={0}
                                    angle={-45}
                                    textAnchor="end"
                                />
                                <YAxis 
                                    tick={{ fontSize: 10, fill: '#94a3b8' }} 
                                    tickLine={false} 
                                    axisLine={false} 
                                />
                                <RechartsTooltip 
                                    cursor={{ fill: '#f8fafc' }} 
                                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)' }} 
                                />
                                <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={32}>
                                    {categoryData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">By Status</h3>
                    <div className="h-72 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={statusPieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value" label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false}>
                                    {statusPieData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                    ))}
                                </Pie>
                                <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 mt-4">
                        {statusPieData.map((entry, index) => (
                            <div key={entry.name} className="flex items-center gap-1.5 text-xs text-gray-600">
                                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}></div>
                                {entry.name} ({entry.value})
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Department distribution */}
            {deptData.length > 0 && (
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">By Department</h3>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={deptData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                                <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
                                <RechartsTooltip cursor={{ fill: '#f9fafb' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={32} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Complaints Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                        <h3 className="text-lg font-bold text-gray-900">All Complaints ({filteredComplaints.length})</h3>
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="relative">
                                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                                <input type="text" placeholder="Search..." className="pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary-500 focus:border-primary-500 w-44" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                            </div>
                            <select value={filterDept} onChange={e => setFilterDept(e.target.value)} className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-1 focus:ring-primary-500">
                                <option value="ALL">All Depts</option>
                                {departments.map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-1 focus:ring-primary-500">
                                <option value="ALL">All Status</option>
                                {['SUBMITTED', 'VALIDATED', 'CATEGORIZED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'DUMPED', 'CLOSED'].map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                            </select>
                            <select value={filterPriority} onChange={e => setFilterPriority(e.target.value)} className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-1 focus:ring-primary-500">
                                <option value="ALL">All Priority</option>
                                {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                        </div>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ID</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Department</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Priority</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-4"><span className="sr-only">View</span></th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                            {filteredComplaints.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="px-6 py-12 text-center text-gray-500">No complaints match your filters.</td>
                                </tr>
                            ) : (
                                filteredComplaints.slice(0, 100).map(c => (
                                    <tr key={c.complaint_id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 text-sm font-medium text-gray-900 font-mono">#{c.complaint_id?.substring(0, 8)}</td>
                                        <td className="px-6 py-4 text-sm text-gray-600">{c.department || '-'}</td>
                                        <td className="px-6 py-4 text-sm text-gray-600">{c.category || '-'}</td>
                                        <td className="px-6 py-4"><PriorityBadge priority={c.priority} /></td>
                                        <td className="px-6 py-4"><ComplaintStatusBadge status={c.status} /></td>
                                        <td className="px-6 py-4 text-sm text-gray-500">{c.created_at ? format(new Date(c.created_at), 'MMM d, yyyy') : '-'}</td>
                                        <td className="px-6 py-4 text-right">
                                            <Link to={`/complaints/${c.complaint_id}`} className="text-primary-600 hover:text-primary-900 text-sm font-semibold transition">View &rarr;</Link>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
