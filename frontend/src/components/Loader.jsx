import { cn } from '../utils/cn';

export const Loader = ({ className, size = 'md' }) => {
    const sizes = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
    };

    return (
        <div className={cn("flex justify-center items-center py-4", className)}>
            <div className={cn(
                "animate-spin rounded-full border-b-2 border-primary-600",
                sizes[size] || sizes.md,
            )}></div>
        </div>
    );
};
