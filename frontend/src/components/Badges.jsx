import { cn } from '../utils/cn';

export const VALID_STATUSES = [
    'SUBMITTED', 'VALIDATED', 'CATEGORIZED', 'ASSIGNED',
    'IN_PROGRESS', 'RESOLVED', 'DUMPED', 'CLOSED'
];

export const ComplaintStatusBadge = ({ status, className }) => {
    const statusColors = {
        SUBMITTED: 'bg-blue-100 text-blue-800 border-blue-200',
        VALIDATED: 'bg-cyan-100 text-cyan-800 border-cyan-200',
        CATEGORIZED: 'bg-purple-100 text-purple-800 border-purple-200',
        ASSIGNED: 'bg-orange-100 text-orange-800 border-orange-200',
        IN_PROGRESS: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        RESOLVED: 'bg-green-100 text-green-800 border-green-200',
        DUMPED: 'bg-red-100 text-red-800 border-red-200',
        CLOSED: 'bg-gray-100 text-gray-800 border-gray-200',
    };

    const defaultColor = 'bg-gray-100 text-gray-800 border-gray-200';
    const colorClass = statusColors[status] || defaultColor;

    return (
        <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium border', colorClass, className)}>
            {status ? status.replace('_', ' ') : 'UNKNOWN'}
        </span>
    );
};

export const PriorityBadge = ({ priority, className }) => {
    const priorityColors = {
        LOW: 'bg-blue-100 text-blue-800',
        MEDIUM: 'bg-yellow-100 text-yellow-800',
        HIGH: 'bg-orange-100 text-orange-800',
        CRITICAL: 'bg-red-100 text-red-800',
    };

    const p = priority?.toUpperCase() || 'LOW';
    const defaultColor = 'bg-gray-100 text-gray-800';
    const colorClass = priorityColors[p] || defaultColor;

    return (
        <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-semibold', colorClass, className)}>
            {p}
        </span>
    );
};
