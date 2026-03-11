import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/api';
import { toast } from 'sonner';
import { ImageUploader } from '../components/ImageUploader';
import { CheckCircle, AlertCircle } from 'lucide-react';
import { PriorityBadge } from '../components/Badges';

export const SubmitComplaint = () => {
    const [description, setDescription] = useState('');
    const [imageUrl, setImageUrl] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [successData, setSuccessData] = useState(null);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!description.trim()) {
            toast.error('Description is required');
            return;
        }

        setIsSubmitting(true);
        try {
            const payload = {
                description,
                ...(imageUrl && { image_url: imageUrl })
            };

            const res = await api.post('/complaint', payload);
            setSuccessData(res.data);
            toast.success('Complaint submitted successfully!');
        } catch (error) {
            console.error(error);
            toast.error('Failed to submit complaint');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (successData) {
        return (
            <div className="max-w-2xl mx-auto mt-10 p-8 bg-white rounded-2xl shadow-lg border border-gray-100 text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-2">Complaint Received!</h2>
                <p className="text-gray-500 mb-8">Your issue has been logged and is being analyzed.</p>

                <div className="bg-gray-50 rounded-xl p-6 text-left mb-8 space-y-4">
                    <div className="flex justify-between items-center border-b pb-4">
                        <span className="text-gray-500">Complaint ID</span>
                        <span className="font-mono font-medium">{successData.complaint_id}</span>
                    </div>
                    <div className="flex justify-between items-center border-b pb-4">
                        <span className="text-gray-500">Department</span>
                        <span className="font-medium">{successData.department}</span>
                    </div>
                    <div className="flex justify-between items-center border-b pb-4">
                        <span className="text-gray-500">Category</span>
                        <span className="font-medium bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                            {successData.category}
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-gray-500">Priority</span>
                        <PriorityBadge priority={successData.priority} className="text-sm px-3 py-1" />
                    </div>
                </div>

                {successData.summary && (
                    <div className="mb-8 text-left bg-blue-50 p-4 rounded-lg border border-blue-100">
                        <div className="flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5" />
                            <div>
                                <h4 className="font-medium text-blue-900 mb-1">AI Summary</h4>
                                <p className="text-sm text-blue-800 leading-relaxed">{successData.summary}</p>
                            </div>
                        </div>
                    </div>
                )}

                <div className="flex justify-center gap-4">
                    <button
                        onClick={() => navigate('/my-complaints')}
                        className="px-6 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
                    >
                        Track Status
                    </button>
                    <button
                        onClick={() => {
                            setSuccessData(null);
                            setDescription('');
                            setImageUrl(null);
                        }}
                        className="px-6 py-2.5 bg-white text-gray-700 font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        Submit Another
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Report an Issue</h1>
                <p className="text-gray-500 mt-2">Help us keep the city clean and safe by reporting municipal issues.</p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-100 space-y-6">
                <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Description
                    </label>
                    <textarea
                        required
                        rows={5}
                        placeholder="Describe the issue in detail (e.g. Broken streetlight on Main St. near the park)"
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-shadow resize-none"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>

                <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Photo Verification <span className="text-gray-400 font-normal">(Optional but recommended)</span>
                    </label>
                    <ImageUploader onUploadSuccess={setImageUrl} />
                </div>

                <div className="pt-4 border-t border-gray-100">
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full py-3.5 px-4 bg-primary-600 text-white text-lg font-medium rounded-xl hover:bg-primary-700 focus:ring-4 focus:ring-primary-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        {isSubmitting ? 'Analyzing & Submitting...' : 'Submit Complaint'}
                    </button>
                </div>
            </form>
        </div>
    );
};
