import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, notificationApi } from '../api/api';
import { Loader } from '../components/Loader';
import { ComplaintStatusBadge, PriorityBadge } from '../components/Badges';
import { useAuthStore } from '../hooks/useAuthStore';
import { format } from 'date-fns';
import { Search, Filter, AlertCircle, FileText, CheckCircle2, Zap, Bell } from 'lucide-react';
import { useNotificationStore } from '../hooks/useNotifications';
import { cn } from '../utils/cn';
import { toast } from 'sonner';

export const StaffDashboard = () => {
    const { user } = useAuthStore();
    const { isConnected } = useNotificationStore();
    const [complaints, setComplaints] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');

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
        const fetchDepartmentComplaints = async () => {
            try {
                const res = await api.get('/admin/complaints/department');
                setComplaints(res.data);
            } catch (error) {
                console.error('Failed to fetch department complaints', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchDepartmentComplaints();
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

    const stats = {
        total: complaints.length,
        pending: complaints.filter(c => ['SUBMITTED', 'VALIDATED', 'CATEGORIZED', 'ASSIGNED'].includes(c.status)).length,
        inProgress: complaints.filter(c => c.status === 'IN_PROGRESS').length,
        resolved: complaints.filter(c => c.status === 'RESOLVED').length,
        closed: complaints.filter(c => c.status === 'CLOSED').length,
        dumped: complaints.filter(c => c.status === 'DUMPED').length,
    };

    const filteredComplaints = complaints.filter(c => {
        const matchesSearch = c.complaint_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (c.description || '').toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'ALL' || c.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    const highPriorityComplaints = complaints.filter(c => 
        (c.priority === 'HIGH' || c.priority === 'CRITICAL') && 
        !['RESOLVED', 'CLOSED', 'DUMPED'].includes(c.status)
    ).sort((a, b) => {
        if (a.priority === 'CRITICAL' && b.priority !== 'CRITICAL') return -1;
        if (a.priority !== 'CRITICAL' && b.priority === 'CRITICAL') return 1;
        return new Date(b.created_at) - new Date(a.created_at);
    });

    if (isLoading) return <Loader size="lg" className="h-64" />;

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Department Dashboard</h1>
                    <p className="text-gray-500 mt-2">Manage and resolve complaints assigned to {user?.username}'s department</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-1 bg-white border border-gray-100 rounded-full shadow-sm">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">{isConnected ? 'Live' : 'Offline'}</span>
                    </div>
                    <button
                        onClick={() => setShowNotifForm(!showNotifForm)}
                        className="px-5 py-2.5 bg-gray-900 text-white font-medium rounded-xl hover:bg-black transition-colors flex items-center gap-2 shadow-lg shadow-gray-200 text-sm"
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

            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
                {[
                    { label: 'Total', value: stats.total, icon: FileText, color: 'text-blue-600', bg: 'bg-blue-200/50' },
                    { label: 'Pending', value: stats.pending, icon: AlertCircle, color: 'text-orange-600', bg: 'bg-orange-200/50' },
                    { label: 'Active', value: stats.inProgress, icon: Zap, color: 'text-yellow-600', bg: 'bg-yellow-200/50' },
                    { label: 'Resolved', value: stats.resolved, icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-200/50' },
                    { label: 'Closed', value: stats.closed, icon: FileText, color: 'text-gray-600', bg: 'bg-gray-200/50' },
                    { label: 'Dumped', value: stats.dumped, icon: Filter, color: 'text-red-600', bg: 'bg-red-200/50' },
                ].map((stat) => (
                    <div key={stat.label} className="bg-white overflow-hidden shadow-sm rounded-2xl border border-gray-100 p-5 flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs font-bold text-gray-400 truncate uppercase tracking-tight">{stat.label}</p>
                            <p className="mt-1 text-2xl font-black text-gray-900">{stat.value}</p>
                        </div>
                        <div className={`p-2.5 rounded-xl ${stat.bg} flex-shrink-0`}>
                            <stat.icon className={`w-5 h-5 ${stat.color}`} />
                        </div>
                    </div>
                ))}
            </div>

            {/* High Priority Alerts */}
            {highPriorityComplaints.length > 0 && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-red-500" />
                        <h2 className="text-xl font-bold text-gray-900">Department Priority Alerts</h2>
                        <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-bold rounded-full">{highPriorityComplaints.length}</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {highPriorityComplaints.slice(0, 6).map(c => (
                            <div key={c.complaint_id} className="bg-white p-5 rounded-2xl border-l-4 border-l-red-500 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                                <div className="flex justify-between items-start mb-3">
                                    <span className="text-xs font-mono font-bold text-gray-400">#{c.complaint_id.substring(0, 8)}</span>
                                    <PriorityBadge priority={c.priority} />
                                </div>
                                <h4 className="font-bold text-gray-900 line-clamp-1 mb-1">{c.category || 'No Category'}</h4>
                                <p className="text-sm text-gray-500 line-clamp-2 mb-4">{c.description || 'No description provided.'}</p>
                                <div className="flex justify-between items-center mt-auto pt-3 border-t border-gray-50">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] uppercase font-bold text-gray-400">Status</span>
                                        <ComplaintStatusBadge status={c.status} className="!px-0 !py-0 !border-none !bg-transparent !text-[12px] font-semibold" />
                                    </div>
                                    <Link to={`/complaints/${c.complaint_id}`} className="p-2 bg-gray-50 hover:bg-red-50 text-gray-400 hover:text-red-500 rounded-lg transition-colors">
                                        <Zap className="w-4 h-4" />
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-4 bg-gray-50/50">
                    <div className="relative w-full sm:max-w-md">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Search className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Search by ID or description..."
                            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm transition-shadow"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                        <Filter className="w-5 h-5 text-gray-400" />
                        <select
                            title="Filter by status"
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-lg"
                        >
                            <option value="ALL">All Statuses</option>
                            <option value="SUBMITTED">Submitted</option>
                            <option value="VALIDATED">Validated</option>
                            <option value="CATEGORIZED">Categorized</option>
                            <option value="ASSIGNED">Assigned</option>
                            <option value="IN_PROGRESS">In Progress</option>
                            <option value="RESOLVED">Resolved</option>
                            <option value="CLOSED">Closed</option>
                            <option value="DUMPED">Dumped</option>
                        </select>
                    </div>
                </div>

                <div className="overflow-x-auto min-h-[400px]">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ID / Date</th>
                                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Priority</th>
                                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Assigned To</th>
                                <th scope="col" className="relative px-6 py-4"><span className="sr-only">View</span></th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                            {filteredComplaints.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                        No complaints found matching criteria.
                                    </td>
                                </tr>
                            ) : (
                                filteredComplaints.map((complaint) => {
                                    const isUrgent = complaint.priority === 'HIGH' || complaint.priority === 'CRITICAL';
                                    const isCritical = complaint.priority === 'CRITICAL';
                                    const isNotResolved = !['RESOLVED', 'CLOSED', 'DUMPED'].includes(complaint.status);

                                    return (
                                        <tr key={complaint.complaint_id} className={cn(
                                            "hover:bg-gray-50 transition-colors",
                                            isUrgent && isNotResolved && "bg-red-50/30"
                                        )}>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2 mb-1">
                                                    {isCritical && isNotResolved && (
                                                        <span className="flex h-2 w-2 rounded-full bg-red-600 animate-ping"></span>
                                                    )}
                                                    <div className="text-sm font-medium text-gray-900">#{complaint.complaint_id.substring(0, 8)}</div>
                                                </div>
                                                <div className="text-xs text-gray-500">{format(new Date(complaint.created_at), 'MMM d, yyyy')}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm text-gray-900">{complaint.category || 'N/A'}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                <PriorityBadge priority={complaint.priority} />
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                <ComplaintStatusBadge status={complaint.status} />
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {complaint.assigned_to ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                        {complaint.assigned_to}
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-400 italic">Unassigned</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <Link to={`/complaints/${complaint.complaint_id}`} className={cn(
                                                    "font-semibold transition-colors",
                                                    isUrgent && isNotResolved ? "text-red-600 hover:text-red-700 underline underline-offset-4" : "text-primary-600 hover:text-primary-900"
                                                )}>
                                                    {isUrgent && isNotResolved ? 'Solve Now →' : 'View →'}
                                                </Link>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
