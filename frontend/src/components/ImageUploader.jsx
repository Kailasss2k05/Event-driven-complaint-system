import { useState, useRef } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../api/api';
import { toast } from 'sonner';

export const ImageUploader = ({ onUploadSuccess, className }) => {
    const [isUploading, setIsUploading] = useState(false);
    const [preview, setPreview] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            toast.error('Please select an image file');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            toast.error('Image must be less than 5MB');
            return;
        }

        const reader = new FileReader();
        reader.onload = () => setPreview(reader.result);
        reader.readAsDataURL(file);

        try {
            setIsUploading(true);
            const formData = new FormData();
            formData.append('file', file);

            const res = await api.post('/complaint/upload-image', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            onUploadSuccess(res.data.image_url);
        } catch (error) {
            console.error('Upload failed:', error);
            toast.error('Failed to upload image');
            setPreview(null);
        } finally {
            setIsUploading(false);
        }
    };

    const handeRemove = () => {
        setPreview(null);
        onUploadSuccess(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className={cn("w-full", className)}>
            {!preview ? (
                <div
                    onClick={() => fileInputRef.current?.click()}
                    className={cn(
                        "border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 transition-colors",
                        isUploading && "opacity-50 pointer-events-none"
                    )}
                >
                    <Upload className="w-8 h-8 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600">
                        {isUploading ? 'Uploading...' : 'Click to upload an image'}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">JPEG, PNG up to 5MB</p>
                </div>
            ) : (
                <div className="relative border rounded-lg overflow-hidden bg-gray-50 h-48 flex items-center justify-center">
                    <img src={preview} alt="Preview" className="max-h-full max-w-full object-contain" />
                    <button
                        type="button"
                        onClick={handeRemove}
                        className="absolute top-2 right-2 p-1 bg-white/90 rounded-full shadow-sm hover:bg-white text-gray-600 hover:text-red-600 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
            )}
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
            />
        </div>
    );
};
