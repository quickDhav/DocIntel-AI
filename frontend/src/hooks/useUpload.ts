'use client';

/* ============================================================
   DocIntel AI — File Upload State Management Hook
   ============================================================ */

import { useState, useCallback, useRef, useEffect } from 'react';
import { UploadJob } from '@/lib/types';
import { uploadFiles, getUploadStatus } from '@/lib/api';

export function useUpload() {
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const addFiles = useCallback((files: File[]) => {
    const newJobs: UploadJob[] = files.map((file) => ({
      file,
      status: 'pending',
      progress: 0,
    }));
    setJobs((prev) => [...prev, ...newJobs]);
  }, []);

  const removeJob = useCallback((index: number) => {
    setJobs((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearCompleted = useCallback(() => {
    setJobs((prev) =>
      prev.filter((j) => j.status !== 'ready' && j.status !== 'error')
    );
  }, []);

  const statusToProgress = (
    status: string
  ): number => {
    switch (status) {
      case 'uploading':
        return 20;
      case 'parsing':
        return 40;
      case 'classifying':
        return 65;
      case 'indexing':
        return 85;
      case 'ready':
        return 100;
      case 'error':
        return 100;
      default:
        return 0;
    }
  };

  const pollStatuses = useCallback(async () => {
    setJobs((currentJobs) => {
      const activeJobs = currentJobs.filter(
        (j) =>
          j.id &&
          j.status !== 'ready' &&
          j.status !== 'error' &&
          j.status !== 'pending'
      );

      if (activeJobs.length === 0) {
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
        setIsUploading(false);
        return currentJobs;
      }

      activeJobs.forEach(async (job) => {
        if (!job.id) return;
        try {
          const info = await getUploadStatus(job.id);
          setJobs((prev) =>
            prev.map((j) =>
              j.id === job.id
                ? {
                    ...j,
                    status: info.status,
                    progress: statusToProgress(info.status),
                    classification: info.classification,
                    error: info.error_message,
                  }
                : j
            )
          );
        } catch {
        }
      });

      return currentJobs;
    });
  }, []);

  const startUpload = useCallback(async () => {
    const pendingJobs = jobs.filter((j) => j.status === 'pending');
    if (pendingJobs.length === 0) return;

    setIsUploading(true);

    setJobs((prev) =>
      prev.map((j) =>
        j.status === 'pending' ? { ...j, status: 'uploading', progress: 10 } : j
      )
    );

    try {
      const files = pendingJobs.map((j) => j.file);
      const response = await uploadFiles(files);

      setJobs((prev) => {
        let idIndex = 0;
        return prev.map((j) => {
          if (
            j.status === 'uploading' &&
            !j.id &&
            idIndex < response.job_ids.length
          ) {
            const id = response.job_ids[idIndex];
            idIndex++;
            return { ...j, id, status: 'parsing', progress: 25 };
          }
          return j;
        });
      });

      if (pollingRef.current) clearInterval(pollingRef.current);
      pollingRef.current = setInterval(pollStatuses, 2000);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Upload failed';
      setJobs((prev) =>
        prev.map((j) =>
          j.status === 'uploading'
            ? { ...j, status: 'error', progress: 100, error: errorMsg }
            : j
        )
      );
      setIsUploading(false);
    }
  }, [jobs, pollStatuses]);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const pendingCount = jobs.filter((j) => j.status === 'pending').length;
  const activeCount = jobs.filter(
    (j) =>
      j.status !== 'ready' &&
      j.status !== 'error' &&
      j.status !== 'pending'
  ).length;

  return {
    jobs,
    isUploading,
    pendingCount,
    activeCount,
    addFiles,
    removeJob,
    startUpload,
    clearCompleted,
  };
}
