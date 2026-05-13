import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadResume } from '../utils/api';
import toast from 'react-hot-toast';

export default function UploadZone({ onUploaded, label = 'Drop your resume here' }) {
  const [uploading, setUploading] = useState(false);
  const [progress,  setProgress]  = useState(0);
  const [done,      setDone]      = useState(null);

  const onDrop = useCallback(async (files) => {
    if (!files.length) return;
    const file = files[0];
    if (file.size > 6 * 1024 * 1024) { toast.error('File must be under 6 MB.'); return; }
    setUploading(true); setProgress(0); setDone(null);
    try {
      const result = await uploadResume(file, setProgress);
      setDone({ name: file.name, ...result });
      onUploaded?.(result);
      toast.success('Resume uploaded and parsed!');
    } catch (err) {
      toast.error(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  }, [onUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div>
      <div {...getRootProps()} className={`dz${isDragActive ? ' on' : ''}`}>
        <input {...getInputProps()} />
        <div className="dz-icon">{uploading ? '⏳' : isDragActive ? '📂' : '📄'}</div>
        {uploading ? (
          <>
            <p className="dz-text">Uploading & parsing…</p>
            <div style={{ width: 200, margin: '10px auto 0' }}>
              <div className="pbar">
                <div className="pfill" style={{ width: `${progress}%`, background: 'var(--accent)' }} />
              </div>
              <p style={{ color: 'var(--txt3)', fontSize: '.73rem', textAlign: 'center', marginTop: 5 }}>{progress}%</p>
            </div>
          </>
        ) : (
          <>
            <p className="dz-text">{label} — <strong>click to browse</strong></p>
            <p className="dz-hint">PDF & DOCX · max 6 MB</p>
          </>
        )}
      </div>
      {done && !uploading && (
        <div className="file-ok">
          ✅ <span>{done.filename}</span>
          <span style={{ color: 'var(--txt3)', fontSize: '.73rem' }}>
            &nbsp;· {done.parsed?.word_count || 0} words
          </span>
        </div>
      )}
    </div>
  );
}
