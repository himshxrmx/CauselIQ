import { useState, useRef } from 'react';
import { X, Upload, FileText, Loader2 } from 'lucide-react';
import { uploadLogs, Incident } from '../api';

interface UploadModalProps {
  onClose: () => void;
  onSuccess: (incident: Incident) => void;
}

export default function UploadModal({ onClose, onSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [codeFile, setCodeFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const codeFileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleCodeFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setCodeFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setIsUploading(true);
      setError(null);
      const res = await uploadLogs(file, codeFile || undefined);
      onSuccess(res.data.incident);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div 
        className="bg-dark-800 border border-white/10 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
          <div>
            <h2 className="text-lg font-semibold text-white">Upload Incident Data</h2>
            <p className="text-xs text-white/40 mt-1">Upload logs and optional source code</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/10 text-white/40 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Logs Upload */}
          <div 
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
              file ? 'border-accent-cyan/30 bg-accent-cyan/5' : 'border-white/10 hover:border-white/30 hover:bg-white/5'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept=".txt,.log,.json" 
            />
            
            {file ? (
              <div className="flex flex-col items-center">
                <FileText className="w-8 h-8 text-accent-cyan mb-2" />
                <p className="text-sm font-medium text-white">{file.name}</p>
                <p className="text-xs text-white/40 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-8 h-8 text-white/20 mb-2" />
                <p className="text-sm font-medium text-white/70">1. Upload Logs (Required)</p>
                <p className="text-xs text-white/40 mt-1">.txt or .log files</p>
              </div>
            )}
          </div>

          {/* Source Code Upload */}
          <div 
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
              codeFile ? 'border-accent-purple/30 bg-accent-purple/5' : 'border-white/10 hover:border-white/30 hover:bg-white/5'
            }`}
            onClick={() => codeFileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={codeFileInputRef} 
              onChange={handleCodeFileChange} 
              className="hidden" 
              accept=".js,.ts,.py,.go,.java,.tsx,.jsx,.cs,.rb,.php,.txt" 
            />
            
            {codeFile ? (
              <div className="flex flex-col items-center">
                <FileText className="w-8 h-8 text-accent-purple mb-2" />
                <p className="text-sm font-medium text-white">{codeFile.name}</p>
                <p className="text-xs text-white/40 mt-1">{(codeFile.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-8 h-8 text-white/20 mb-2" />
                <p className="text-sm font-medium text-white/70">2. Upload Source Code (Optional)</p>
                <p className="text-xs text-white/40 mt-1">Give Agent 2 real code context</p>
              </div>
            )}
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-medium text-white/60 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="px-5 py-2 rounded-xl bg-accent-cyan text-dark-900 text-sm font-semibold hover:bg-accent-cyan/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                'Analyze Logs'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
