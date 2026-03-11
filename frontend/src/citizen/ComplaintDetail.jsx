import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/api';
import { Loader } from '../components/Loader';
import { ComplaintStatusBadge, PriorityBadge, VALID_STATUSES } from '../components/Badges';
import { CheckCircle2, Circle, ArrowLeft, Image as ImageIcon, Briefcase, Tag, Clock, User, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useAuthStore } from '../hooks/useAuthStore';
import { toast } from 'sonner';

export const ComplaintDetail = () => {
    const { id } = useParams();
    const { user } = useAuthStore();
    const [complaint, setComplaint] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isUpdating, setIsUpdating] = useState(false);
    const [updateStatus, setUpdateStatus] = useState('');
    const [assignee, setAssignee] = useState('');

    const fetchComplaint = async () => {
        try {
            const res = await api.get(`/complaint/${id}`);
            setComplaint(res.data);
            setUpdateStatus(res.data.status);
        } catch (error) {
            console.error('Failed to fetch complaint detail', error);
            toast.error('Failed to load complaint details');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (id) fetchComplaint();
    }, [id]);

    const handleUpdateStatus = async () => {
        if (!updateStatus) return;
        setIsUpdating(true);
        try {
            await api.put(`/complaint/${id}/status`, {
                status: updateStatus,
                notes: `Status updated to ${updateStatus}`
            });
            toast.success('Status updated');
            fetchComplaint();
        } catch (error) {
            toast.error('Failed to update status');
        } finally {
            setIsUpdating(false);
        }
    };

    const handleAssign = async () => {
        if (!assignee) return;
        setIsUpdating(true);
        try {
            await api.put(`/admin/complaint/${id}/assign`, {
                assigned_to: assignee,
                target_department: '',
                notes: 'Assigned via staff dashboard'
            });
            toast.success('Complaint assigned');
            fetchComplaint();
            setAssignee('');
        } catch (error) {
            toast.error('Failed to assign complaint');
        } finally {
            setIsUpdating(false);
        }
    };

    if (isLoading) return <Loader size="lg" className="h-64" />;
    if (!complaint) return (
        <div className="text-center py-20">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900">Complaint not found</h3>
        </div>
    );

    const isStaff = user?.role === 'department_admin';
    const isAdmin = user?.role === 'super_admin';
    const currentStepIndex = VALID_STATUSES.indexOf(complaint.status);

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-12">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link
                    to={isStaff ? '/staff' : isAdmin ? '/admin' : '/my-complaints'}
                    className="p-2 bg-white border border-gray-200 rounded-full hover:bg-gray-50 transition-colors text-gray-500"
                >
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                        Complaint #{complaint.complaint_id?.substring(0, 8)}
                        <ComplaintStatusBadge status={complaint.status} className="text-sm px-3 py-1" />
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">
                        Submitted on {complaint.created_at ? format(new Date(complaint.created_at), 'MMMM d, yyyy h:mm a') : 'N/A'}
                    </p>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <h3 className="text-sm font-semibold text-gray-900 mb-6 uppercase tracking-wider">Status Progression</h3>
                <div className="flex items-center justify-between w-full relative">
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 lg:h-1.5 bg-gray-100 rounded-full"></div>
                    <div
                        className="absolute left-0 top-1/2 -translate-y-1/2 h-1 lg:h-1.5 bg-primary-500 rounded-full transition-all duration-500"
                        style={{ width: `${(Math.max(0, currentStepIndex) / (VALID_STATUSES.length - 1)) * 100}%` }}
                    ></div>
                    {VALID_STATUSES.map((status, index) => {
                        const isCompleted = index <= currentStepIndex;
                        const isCurrent = index === currentStepIndex;
                        return (
                            <div key={status} className="relative z-10 flex flex-col items-center group">
                                <div className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center transition-colors duration-300 ${isCompleted ? 'bg-primary-600 text-white shadow-md shadow-primary-200' : 'bg-gray-200 text-gray-400'}`}>
                                    {isCompleted ? <CheckCircle2 className="w-4 h-4 sm:w-5 sm:h-5" /> : <Circle className="w-3 h-3 sm:w-4 sm:h-4 fill-current" />}
                                </div>
                                <span className={`hidden sm:block absolute -bottom-8 text-[10px] font-medium uppercase tracking-widest text-center whitespace-nowrap transition-colors ${isCurrent ? 'text-primary-700 font-bold' : isCompleted ? 'text-gray-900' : 'text-gray-400'}`}>
                                    {status.replace('_', ' ')}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-8">
                {/* Left column */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Description */}
                    <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Original Description</h3>
                        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{complaint.description}</p>

                        {complaint.description_en && complaint.description_en !== complaint.description && (
                            <div className="mt-6 pt-6 border-t border-gray-100">
                                <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">English Translation</h4>
                                <p className="text-gray-700 italic border-l-4 border-gray-200 pl-4">{complaint.description_en}</p>
                            </div>
                        )}

                        {complaint.summary && (
                            <div className="mt-6 p-4 bg-primary-50 border border-primary-100 rounded-xl">
                                <h4 className="text-sm font-semibold text-primary-900 flex items-center gap-2 mb-2">
                                    <Briefcase className="w-4 h-4" /> AI Generated Summary
                                </h4>
                                <p className="text-primary-800 text-sm leading-relaxed">{complaint.summary}</p>
                            </div>
                        )}
                    </div>

                    {/* Image */}
                    {complaint.image_url && (
                        <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-100">
                            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                <ImageIcon className="w-5 h-5 text-gray-400" /> Attached Photo
                            </h3>
                            <div className="rounded-xl overflow-hidden bg-gray-50 border border-gray-200 flex items-center justify-center min-h-[300px]">
                                <img
                                    src={complaint.image_url.startsWith('http') ? complaint.image_url : `http://localhost:8000${complaint.image_url}`}
                                    alt="Complaint"
                                    className="max-h-[500px] w-auto object-contain"
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23f3f4f6" width="400" height="300"/><text x="50%" y="50%" text-anchor="middle" fill="%239ca3af" font-size="16">Image Not Available</text></svg>';
                                    }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Right column */}
                <div className="space-y-6">
                    {/* Metadata Card */}
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-5">Details</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center py-2 border-b border-gray-50">
                                <span className="text-gray-500 flex items-center gap-2 text-sm"><Tag className="w-4 h-4" /> Category</span>
                                <span className="font-medium text-gray-900">{complaint.category || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-50">
                                <span className="text-gray-500 flex items-center gap-2 text-sm"><Briefcase className="w-4 h-4" /> Department</span>
                                <span className="font-medium text-gray-900">{complaint.department || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-50">
                                <span className="text-gray-500 flex items-center gap-2 text-sm"><AlertCircle className="w-4 h-4" /> Priority</span>
                                <PriorityBadge priority={complaint.priority} />
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-50">
                                <span className="text-gray-500 flex items-center gap-2 text-sm"><User className="w-4 h-4" /> Assigned To</span>
                                <span className="font-medium text-gray-900">{complaint.assigned_to || 'Unassigned'}</span>
                            </div>
                            <div className="flex justify-between items-center py-2">
                                <span className="text-gray-500 flex items-center gap-2 text-sm"><Clock className="w-4 h-4" /> Last Updated</span>
                                <span className="font-medium text-gray-900 text-sm">
                                    {complaint.updated_at ? format(new Date(complaint.updated_at), 'MMM d, h:mm a') : 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Staff Actions */}
                    {isStaff && (
                        <div className="bg-gradient-to-b from-gray-50 to-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-6">
                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider border-b pb-3">Staff Actions</h3>
                            <div className="space-y-3">
                                <label className="block text-sm font-medium text-gray-700">Update Status</label>
                                <div className="flex gap-2">
                                    <select
                                        value={updateStatus}
                                        onChange={(e) => setUpdateStatus(e.target.value)}
                                        className="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                    >
                                        {['IN_PROGRESS', 'RESOLVED', 'DUMPED', 'CLOSED'].map(s => (
                                            <option key={s} value={s}>{s.replace('_', ' ')}</option>
                                        ))}
                                    </select>
                                    <button
                                        onClick={handleUpdateStatus}
                                        disabled={isUpdating || updateStatus === complaint.status}
                                        className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 transition"
                                    >
                                        Save
                                    </button>
                                </div>
                            </div>
                            <div className="space-y-3 pt-4 border-t border-gray-200">
                                <label className="block text-sm font-medium text-gray-700">Assign Officer</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={assignee}
                                        onChange={(e) => setAssignee(e.target.value)}
                                        placeholder="Officer Name"
                                        className="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                    />
                                    <button
                                        onClick={handleAssign}
                                        disabled={isUpdating || !assignee.trim()}
                                        className="px-4 py-2 bg-gray-800 text-white rounded-lg text-sm font-medium hover:bg-gray-900 disabled:opacity-50 transition"
                                    >
                                        Assign
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
