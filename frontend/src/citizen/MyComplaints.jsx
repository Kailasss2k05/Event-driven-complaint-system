import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, notificationApi } from '../api/api';
import { Loader } from '../components/Loader';
import { ComplaintStatusBadge, PriorityBadge } from '../components/Badges';
import { Calendar, MapPin, Tag, Bell } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export const MyComplaints = () => {
    const [complaints, setComplaints] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

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
        const fetchComplaints = async () => {
            try {
                const res = await api.get('/complaints/me');
                setComplaints(res.data);
            } catch (error) {
                console.error('Failed to fetch complaints', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchComplaints();
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

    const [filterStatus, setFilterStatus] = useState('ALL');

    const stats = {
        total: complaints.length,
        active: complaints.filter(c => !['RESOLVED', 'CLOSED', 'DUMPED'].includes(c.status)).length,
        resolved: complaints.filter(c => c.status === 'RESOLVED').length,
        closed: complaints.filter(c => c.status === 'CLOSED').length,
        dumped: complaints.filter(c => c.status === 'DUMPED').length,
    };

    const filteredComplaints = complaints.filter(c => {
        if (filterStatus === 'ALL') return true;
        if (filterStatus === 'ACTIVE') return !['RESOLVED', 'CLOSED', 'DUMPED'].includes(c.status);
        return c.status === filterStatus;
    });

    if (isLoading) return <Loader size="lg" className="h-64" />;

    return (
        <div className="max-w-5xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">My Complaints</h1>
                    <p className="text-gray-500 mt-1">Track the status of your reported issues</p>
                </div>
                <div className="flex items-center gap-3">
                    <select 
                        value={filterStatus} 
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="bg-white border border-gray-200 rounded-xl px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                        <option value="ALL">All Complaints</option>
                        <option value="ACTIVE">Active</option>
                        <option value="RESOLVED">Resolved</option>
                        <option value="CLOSED">Closed</option>
                        <option value="DUMPED">Dumped</option>
                    </select>
                    <button
                        onClick={() => setShowNotifForm(!showNotifForm)}
                        className="px-5 py-2 bg-gray-900 text-white font-bold rounded-xl hover:bg-black hover:scale-105 transition-all shadow-lg flex items-center gap-2"
                    >
                        <Bell className="w-4 h-4" /> Send Notification
                    </button>
                    <Link
                        to="/submit"
                        className="px-5 py-2 bg-primary-600 text-white font-bold rounded-xl hover:bg-primary-700 hover:scale-105 transition-all shadow-lg shadow-primary-200 flex items-center gap-2"
                    >
                        <Tag className="w-4 h-4" /> New Report
                    </Link>
                </div>
            </div>

            {/* Notification Form Modal */}
            {showNotifForm && (
                <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-200 animate-in fade-in duration-200 mb-8">
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

            {/* Status Summary */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
                {[
                    { label: 'Total', value: stats.total, color: 'blue' },
                    { label: 'Active', value: stats.active, color: 'orange' },
                    { label: 'Resolved', value: stats.resolved, color: 'green' },
                    { label: 'Closed', value: stats.closed, color: 'gray' },
                    { label: 'Dumped', value: stats.dumped, color: 'red' },
                ].map((stat) => (
                    <div 
                        key={stat.label} 
                        className={`bg-${stat.color}-50 border border-${stat.color}-100 rounded-2xl p-4 text-center cursor-pointer hover:scale-105 transition-transform`}
                        onClick={() => setFilterStatus(stat.label === 'Active' ? 'ACTIVE' : (stat.label === 'Total' ? 'ALL' : stat.label.toUpperCase()))}
                    >
                        <p className={`text-[10px] font-black uppercase tracking-widest text-${stat.color}-600 mb-1`}>{stat.label}</p>
                        <p className={`text-2xl font-black text-${stat.color}-900`}>{stat.value}</p>
                    </div>
                ))}
            </div>

            {filteredComplaints.length === 0 ? (
                <div className="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-gray-100 shadow-inner">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-slate-50 mb-6 group">
                        <Tag className="w-10 h-10 text-gray-300 group-hover:text-primary-400 transition-colors" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">No complaints found</h3>
                    <p className="text-gray-500 mb-8 max-w-xs mx-auto text-sm">You don't have any complaints in the "{filterStatus.toLowerCase()}" status.</p>
                    <button 
                        onClick={() => setFilterStatus('ALL')}
                        className="text-primary-600 font-bold hover:text-primary-700 uppercase tracking-widest text-xs"
                    >
                        View all reports &rarr;
                    </button>
                </div>
            ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {filteredComplaints.map((complaint) => (
                        <Link
                            key={complaint.complaint_id}
                            to={`/complaints/${complaint.complaint_id}`}
                            className="group bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-all duration-200"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <span className="text-xs font-mono text-gray-400 bg-gray-50 px-2 py-1 rounded">
                                    #{complaint.complaint_id.substring(0, 8)}
                                </span>
                                <ComplaintStatusBadge status={complaint.status} />
                            </div>

                            <h3 className="font-semibold text-gray-900 mb-2 line-clamp-1 group-hover:text-primary-600 transition-colors">
                                {complaint.category || 'Uncategorized'}
                            </h3>

                            <p className="text-sm text-gray-600 mb-5 line-clamp-2 h-10">
                                {complaint.summary || complaint.description_en || complaint.description}
                            </p>

                            <div className="space-y-3 pt-4 border-t border-gray-50">
                                <div className="flex items-center text-xs text-gray-500 gap-2">
                                    <Calendar className="w-4 h-4 text-gray-400" />
                                    {format(new Date(complaint.created_at), 'MMM d, yyyy - h:mm a')}
                                </div>
                                <div className="flex justify-between items-center">
                                    <div className="flex items-center text-xs text-gray-500 gap-2">
                                        <MapPin className="w-4 h-4 text-gray-400" />
                                        <span className="truncate max-w-[120px]">{complaint.department || 'Pending'}</span>
                                    </div>
                                    <PriorityBadge priority={complaint.priority} />
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
};
