"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Upload, FileText, Clock, CheckCircle, AlertCircle, Settings, Users, Download } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { UploadArea } from "@/components/ui/upload-area"
import { TrustScoreBadge } from "@/components/ui/trust-score-badge"
import { useAuthStore } from "@/stores/auth"
import { jobsAPI, Job } from "@/lib/api"
import { formatDate, formatBytes, cn } from "@/lib/utils"
import Link from "next/link"

export function DashboardPage() {
  const { user, logout } = useAuthStore()
  const [isUploading, setIsUploading] = useState(false)

  const { data: jobs, isLoading, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => jobsAPI.getJobs().then(res => res.data),
    refetchInterval: 10000
  })

  const handleFileSelect = async (file: File) => {
    setIsUploading(true)
    try {
      await jobsAPI.uploadFile(file, (progress) => {
        console.log(`Upload progress: ${progress}%`)
      })
      // Refetch jobs to get the new job
      await refetch()
    } catch (error) {
      console.error("Upload failed:", error)
    } finally {
      setIsUploading(false)
    }
  }

  const getStatusIcon = (status: Job["status"]) => {
    switch (status) {
      case "queued":
        return <Clock className="w-5 h-5 text-warning" />
      case "processing":
        return <div className="w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
      case "done":
        return <CheckCircle className="w-5 h-5 text-success" />
      case "failed":
        return <AlertCircle className="w-5 h-5 text-danger" />
      default:
        return <FileText className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: Job["status"]) => {
    switch (status) {
      case "queued":
        return "text-warning bg-warning/10"
      case "processing":
        return "text-brand-600 bg-brand-10"
      case "done":
        return "text-success bg-success/10"
      case "failed":
        return "text-danger bg-danger/10"
      default:
        return "text-gray-400 bg-gray-100"
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-semibold text-brand-900">Yantra AI</h1>
              </Link>

              <nav className="hidden md:flex items-center gap-6">
                <Link href="/dashboard" className="text-sm font-medium text-brand-600">
                  Dashboard
                </Link>
                {user?.role === 'reviewer' && (
                  <Link href="/review" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                    Review Queue
                  </Link>
                )}
                {user?.role === 'admin' && (
                  <>
                    <Link href="/admin" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                      Admin
                    </Link>
                    <Link href="/audit" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                      Audit
                    </Link>
                  </>
                )}
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {user?.email}
              </span>
              <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                {user?.role}
              </span>
              <Button variant="outline" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-8"
        >
          {/* Welcome Section */}
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold text-brand-900">
              Welcome back, {user?.email?.split('@')[0]}!
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Transform your scanned documents into structured data with AI-powered OCR,
              trust scoring, and automated PII redaction.
            </p>
          </div>

          {/* Upload Section */}
          <div className="max-w-2xl mx-auto">
            <UploadArea
              onFileSelect={handleFileSelect}
              disabled={isUploading}
              className="h-64"
            />
          </div>

          {/* Jobs List */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-brand-900">Your Documents</h2>
              {jobs && jobs.length > 0 && (
                <Button variant="outline" onClick={() => refetch()}>
                  Refresh
                </Button>
              )}
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : jobs && jobs.length > 0 ? (
              <div className="grid gap-4">
                {jobs.map((job, index) => (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-soft transition-shadow"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {getStatusIcon(job.status)}
                        <div>
                          <h3 className="font-medium text-gray-900">{job.original_filename}</h3>
                          <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                            <span>Uploaded {formatDate(job.created_at)}</span>
                            <span>•</span>
                            <span>Page {job.page_number || 1}</span>
                            {job.avg_trust_score && (
                              <>
                                <span>•</span>
                                <TrustScoreBadge score={job.avg_trust_score} size="sm" showTooltip={false} />
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className={cn(
                          "px-3 py-1 text-xs font-medium rounded-full",
                          getStatusColor(job.status)
                        )}>
                          {job.status}
                        </span>

                        {job.status === "done" && (
                          <Link href={`/jobs/${job.id}`}>
                            <Button size="sm">
                              View Results
                            </Button>
                          </Link>
                        )}

                        {job.status === "done" && job.redacted_path && (
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-2" />
                            Download
                          </Button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
                <p className="text-gray-600">Upload your first document to get started</p>
              </div>
            )}
          </div>
        </motion.div>
      </main>
    </div>
  )
}
