import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuthStore';
import { toast } from 'sonner';
import { Shield, ArrowRight, Lock, User, Mail } from 'lucide-react';
import { motion } from 'framer-motion';

export const Signup = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { signup, isLoading } = useAuthStore();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const role = await signup(username, email, password);
            toast.success('Account created successfully!');

            switch (role) {
                case 'user': navigate('/my-complaints'); break;
                case 'department_admin': navigate('/staff'); break;
                case 'super_admin': navigate('/admin'); break;
                default: navigate('/');
            }
        } catch (error) {
            toast.error(error?.response?.data?.detail || 'Failed to create account');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-slate-950 px-4">
            {/* Animated Background Gradients */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px] animate-pulse"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-600/20 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }}></div>
            </div>

            <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full max-w-[1000px] flex flex-col lg:flex-row rounded-[2.5rem] overflow-hidden shadow-2xl shadow-blue-500/10 border border-white/10 bg-slate-900/40 backdrop-blur-2xl"
            >
                {/* Left Panel - Branding */}
                <div className="hidden lg:flex flex-1 flex-col justify-center p-16 bg-gradient-to-br from-blue-600/5 to-purple-600/5 border-r border-white/5">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center border border-blue-400/20 mb-8 shadow-inner"
                    >
                        <Shield className="w-8 h-8 text-blue-400" />
                    </motion.div>
                    
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <h1 className="text-6xl font-black text-white mb-6 leading-[1.1] tracking-tighter">
                            Civic<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">Resolve</span>
                        </h1>
                        <p className="text-xl text-slate-400 leading-relaxed mb-12 font-medium">
                            Join the platform fixing cities through crowdsourced transparency and AI routing.
                        </p>
                    </motion.div>

                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="flex flex-wrap gap-4"
                    >
                        {[
                            { label: 'Citizen First', color: 'blue' },
                            { label: 'Transparent', color: 'indigo' },
                            { label: 'Quick Impact', color: 'purple' },
                        ].map((tag, i) => (
                            <span key={i} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest bg-blue-500/10 text-blue-400 border border-blue-400/20 shadow-sm`}>
                                {tag.label}
                            </span>
                        ))}
                    </motion.div>
                </div>

                {/* Right Panel - Form */}
                <div className="flex-1 p-8 sm:p-16 flex flex-col justify-center bg-transparent relative">
                    <div className="mb-8 text-center lg:text-left">
                        <h2 className="text-4xl font-bold text-white mb-3">Sign Up</h2>
                        <p className="text-slate-400 font-medium">Create your citizen account to get started.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-300 ml-1">Username</label>
                            <div className="relative group">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-blue-400 transition-all duration-300" />
                                <input
                                    type="text"
                                    required
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full bg-slate-800/40 border-2 border-slate-700/50 rounded-2xl py-3 pl-12 pr-6 text-white placeholder-slate-600 focus:outline-none focus:ring-0 focus:border-blue-500 transition-all font-medium"
                                    placeholder="Username"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-300 ml-1">Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-blue-400 transition-all duration-300" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-slate-800/40 border-2 border-slate-700/50 rounded-2xl py-3 pl-12 pr-6 text-white placeholder-slate-600 focus:outline-none focus:ring-0 focus:border-blue-500 transition-all font-medium"
                                    placeholder="name@example.com"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-300 ml-1">Secure Key</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-blue-400 transition-all duration-300" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-slate-800/40 border-2 border-slate-700/50 rounded-2xl py-3 pl-12 pr-6 text-white placeholder-slate-600 focus:outline-none focus:ring-0 focus:border-blue-500 transition-all font-medium"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <motion.button
                            whileHover={{ scale: 1.01, translateY: -2 }}
                            whileTap={{ scale: 0.98 }}
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-indigo-500 text-white font-black text-lg py-4 px-6 rounded-2xl shadow-xl shadow-blue-600/20 flex items-center justify-center gap-3 disabled:opacity-50 transition-all mt-6 uppercase tracking-widest"
                        >
                            {isLoading ? (
                                <div className="w-6 h-6 border-[3px] border-white/30 border-t-white rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    Create Account <ArrowRight className="w-6 h-6" />
                                </>
                            )}
                        </motion.button>
                    </form>

                    <div className="mt-6 text-center text-slate-400">
                        Already have an account?{' '}
                        <Link to="/login" className="text-blue-400 hover:text-blue-300 font-semibold transition-colors">
                            Log in
                        </Link>
                    </div>

                    <div className="mt-8 text-center flex flex-col gap-2">
                        <p className="text-slate-600 text-[10px] font-bold uppercase tracking-[0.2em]">
                            System Security Level: High
                        </p>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};
