import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/api';
import { Loader } from '../components/Loader';
import { ComplaintStatusBadge, PriorityBadge } from '../components/Badges';
import { Calendar, MapPin, Tag } from 'lucide-react';
import { format } from 'date-fns';

export const MyComplaints = () => {
    const [complaints, setComplaints] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

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

    if (isLoading) return <Loader size="lg" className="h-64" />;

    return (
        <div className="max-w-5xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">My Complaints</h1>
                    <p className="text-gray-500 mt-1">Track the status of your reported issues</p>
                </div>
                <Link
                    to="/submit"
                    className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
                >
                    New Report
                </Link>
            </div>

            {complaints.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-300">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-50 mb-4">
                        <Tag className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No complaints yet</h3>
                    <p className="text-gray-500 mb-6">You haven't reported any issues to the municipality.</p>
                    <Link to="/submit" className="text-primary-600 font-medium hover:text-primary-700">
                        Submit your first report &rarr;
                    </Link>
                </div>
            ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {complaints.map((complaint) => (
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
