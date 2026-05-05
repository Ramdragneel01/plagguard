import { Shield } from 'lucide-react';

export function Header() {
    return (
        <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
            <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
                <div className="p-2 bg-brand-600 rounded-xl">
                    <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h1 className="text-xl font-bold tracking-tight">
                        Plag<span className="text-brand-400">Guard</span>
                    </h1>
                    <p className="text-xs text-slate-500">
                        Plagiarism Detection · AI Detection · Text Humanization
                    </p>
                </div>
            </div>
        </header>
    );
}
