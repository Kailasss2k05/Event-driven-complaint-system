import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/api';
import { Loader } from '../components/Loader';
import { ComplaintStatusBadge, PriorityBadge } from '../components/Badges';
import { useAuthStore } from '../hooks/useAuthStore';
import { format } from 'date-fns';
import { Search, Filter, AlertCircle, FileText, CheckCircle2, Zap } from 'lucide-react';
import { useNotificationStore } from '../hooks/useNotifications';

export const StaffDashboard = () => {
    const { user } = useAuthStore();
    const { isConnected } = useNotificationStore();
    const [complaints, setComplaints] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');

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

    const stats = {
        total: complaints.length,
        pending: complaints.filter(c => ['SUBMITTED', 'VALIDATED', 'CATEGORIZED', 'ASSIGNED'].includes(c.status)).length,
        inProgress: complaints.filter(c => c.status === 'IN_PROGRESS').length,
        resolved: complaints.filter(c => c.status === 'RESOLVED').length,
    };

    const filteredComplaints = complaints.filter(c => {
        const matchesSearch = c.complaint_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (c.description || '').toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'ALL' || c.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    if (isLoading) return <Loader size="lg" className="h-64" />;

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Department Dashboard</h1>
                    <p className="text-gray-500 mt-2">Manage and resolve complaints assigned to {user?.username}'s department</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-white border border-gray-100 rounded-full shadow-sm">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">{isConnected ? 'Live' : 'Offline'}</span>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {[
                    { label: 'Total Complaints', value: stats.total, icon: FileText, color: 'text-blue-600', bg: 'bg-blue-100' },
                    { label: 'Pending Action', value: stats.pending, icon: AlertCircle, color: 'text-orange-600', bg: 'bg-orange-100' },
                    { label: 'In Progress', value: stats.inProgress, icon: Filter, color: 'text-yellow-600', bg: 'bg-yellow-100' },
                    { label: 'Resolved', value: stats.resolved, icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-100' },
                ].map((stat) => (
                    <div key={stat.label} className="bg-white overflow-hidden shadow-sm rounded-2xl border border-gray-100 p-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500 truncate">{stat.label}</p>
                            <p className="mt-1 text-3xl font-semibold text-gray-900">{stat.value}</p>
                        </div>
                        <div className={`p-3 rounded-xl ${stat.bg}`}>
                            <stat.icon className={`w-6 h-6 ${stat.color}`} />
                        </div>
                    </div>
                ))}
            </div>

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
                                filteredComplaints.map((complaint) => (
                                    <tr key={complaint.complaint_id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">#{complaint.complaint_id.substring(0, 8)}</div>
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
                                            <Link to={`/complaints/${complaint.complaint_id}`} className="text-primary-600 hover:text-primary-900 font-semibold transition-colors">
                                                View &rarr;
                                            </Link>
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
