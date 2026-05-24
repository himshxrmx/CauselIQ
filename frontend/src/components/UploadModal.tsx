import { useState, useRef } from 'react';
import { X, Upload, FileText, Loader2 } from 'lucide-react';
import { uploadLogs, Incident } from '../api';

interface UploadModalProps {
  onClose: () => void;
  onSuccess: (incident: Incident) => void;
}

export default function UploadModal({ onClose, onSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setIsUploading(true);
      setError(null);
      const res = await uploadLogs(file);
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
            <h2 className="text-lg font-semibold text-white">Upload Log File</h2>
            <p className="text-xs text-white/40 mt-1">Upload raw logs (.txt, .log) for AI analysis</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/10 text-white/40 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div 
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
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
                <FileText className="w-10 h-10 text-accent-cyan mb-3" />
                <p className="text-sm font-medium text-white">{file.name}</p>
                <p className="text-xs text-white/40 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-10 h-10 text-white/20 mb-3" />
                <p className="text-sm font-medium text-white/70">Click to browse or drag and drop</p>
                <p className="text-xs text-white/40 mt-1">Plain text log files (max 5MB)</p>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="mt-6 flex justify-end gap-3">
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
