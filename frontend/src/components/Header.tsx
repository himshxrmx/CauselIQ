import { Zap, Plus, Upload } from 'lucide-react';

interface HeaderProps {
  onSimulate: () => void;
  onUpload: () => void;
}

export default function Header({ onSimulate, onUpload }: HeaderProps) {
  return (
    <header className="border-b border-white/5 bg-dark-900/80 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center shadow-lg shadow-accent-cyan/20">
            <Zap className="w-5 h-5 text-dark-900" strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">
              Cause<span className="text-accent-cyan">IQ</span>
            </h1>
            <p className="text-[10px] text-white/30 -mt-0.5 tracking-wider uppercase font-medium">
              AI Root Cause Analyzer
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs text-white/40 mr-2">
            <span className="status-dot completed" />
            <span>System Operational</span>
          </div>
          
          <button
            onClick={onUpload}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-800 border border-white/10 text-white/70 text-sm font-medium hover:bg-white/5 hover:text-white transition-all duration-300 cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Logs</span>
          </button>
          
          <button
            id="simulate-btn"
            onClick={onSimulate}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-accent-cyan/10 to-accent-purple/10 border border-accent-cyan/20 text-accent-cyan text-sm font-medium hover:from-accent-cyan/20 hover:to-accent-purple/20 hover:border-accent-cyan/40 transition-all duration-300 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Simulate Incident</span>
          </button>
        </div>
      </div>
    </header>
  );
}
