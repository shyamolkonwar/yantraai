"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/lib/utils"

interface UploadAreaProps {
  onFileSelect: (file: File) => void
  accept?: string
  maxSize?: number // in bytes
  disabled?: boolean
  className?: string
}

interface FileUploadState {
  file: File | null
  status: "idle" | "uploading" | "success" | "error"
  progress: number
  error: string | null
}

export function UploadArea({
  onFileSelect,
  accept = "application/pdf",
  maxSize = 50 * 1024 * 1024, // 50MB
  disabled = false,
  className
}: UploadAreaProps) {
  const [uploadState, setUploadState] = useState<FileUploadState>({
    file: null,
    status: "idle",
    progress: 0,
    error: null
  })
  const [isDragOver, setIsDragOver] = useState(false)

  const handleFileSelect = useCallback((file: File) => {
    // Validate file type
    if (accept && !file.type.includes("pdf")) {
      setUploadState({
        file: null,
        status: "error",
        progress: 0,
        error: "Only PDF files are allowed"
      })
      return
    }

    // Validate file size
    if (file.size > maxSize) {
      setUploadState({
        file: null,
        status: "error",
        progress: 0,
        error: `File size must be less than ${(maxSize / 1024 / 1024).toFixed(1)}MB`
      })
      return
    }

    setUploadState({
      file,
      status: "idle",
      progress: 0,
      error: null
    })

    onFileSelect(file)
  }, [accept, maxSize, onFileSelect])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [disabled, handleFileSelect])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  const clearError = useCallback(() => {
    setUploadState({
      file: null,
      status: "idle",
      progress: 0,
      error: null
    })
  }, [])

  return (
    <motion.div
      className={cn(
        "relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200",
        isDragOver && "border-brand-400 bg-brand-50 scale-[1.02]",
        uploadState.status === "error" && "border-danger bg-danger/10",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      animate={isDragOver ? "active" : "idle"}
      variants={{
        idle: { scale: 1 },
        active: { scale: 1.02 }
      }}
    >
      <AnimatePresence mode="wait">
        {uploadState.status === "error" && uploadState.error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center justify-center gap-2 text-danger mb-4"
          >
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{uploadState.error}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearError}
              className="ml-2 h-auto p-1"
            >
              <X className="w-4 h-4" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      <input
        type="file"
        accept={accept}
        onChange={handleFileInputChange}
        disabled={disabled}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
      />

      <motion.div
        className="flex flex-col items-center space-y-4"
        animate={{
          scale: isDragOver ? 1.1 : 1,
        }}
        transition={{ duration: 0.2 }}
      >
        <div className={cn(
          "w-16 h-16 rounded-full flex items-center justify-center transition-colors",
          isDragOver ? "bg-brand-100 text-brand-600" : "bg-gray-100 text-gray-400"
        )}>
          {uploadState.status === "success" ? (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", duration: 0.5 }}
            >
              <CheckCircle className="w-8 h-8 text-success" />
            </motion.div>
          ) : (
            <Upload className="w-8 h-8" />
          )}
        </div>

        <div className="space-y-2">
          <h3 className="text-lg font-medium text-gray-900">
            {uploadState.status === "success" ? "File uploaded successfully!" : "Upload a document"}
          </h3>
          <p className="text-sm text-gray-600">
            {uploadState.status === "success"
              ? `${uploadState.file?.name} has been uploaded and is being processed.`
              : "Drag and drop a PDF file here, or click to select"
            }
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <FileText className="w-4 h-4" />
            <span>PDF only</span>
          </div>
          <div>Max {(maxSize / 1024 / 1024).toFixed(1)}MB</div>
        </div>

        {uploadState.status !== "success" && (
          <Button variant="outline" disabled={disabled}>
            Choose File
          </Button>
        )}
      </motion.div>

      {/* Subtle pulse animation when idle */}
      {uploadState.status === "idle" && !disabled && (
        <motion.div
          className="absolute inset-0 rounded-xl border-2 border-brand-400 pointer-events-none"
          animate={{ opacity: [0, 0.5, 0] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
    </motion.div>
  )
}