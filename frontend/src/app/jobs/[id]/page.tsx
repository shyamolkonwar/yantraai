"use client"

import { useState, useCallback, useMemo } from "react"
import { motion } from "framer-motion"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, Download, Eye, EyeOff, Share2, FileJson, History } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { PDFViewer } from "@/components/ui/pdf-viewer"
import { FieldList } from "@/components/ui/field-list"
import { jobsAPI, Job, JobResult, Region } from "@/lib/api"
import { toast } from "sonner"
import Link from "next/link"

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string

  const [currentPage, setCurrentPage] = useState(1)
  const [selectedRegionId, setSelectedRegionId] = useState<string>()
  const [searchTerm, setSearchTerm] = useState("")
  const [trustFilter, setTrustFilter] = useState<"all" | "high" | "medium" | "low">("all")
  const [showRedactions, setShowRedactions] = useState(false)

  // Fetch job details
  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => jobsAPI.getJob(jobId).then(res => res.data),
  })

  // Fetch job results (including regions)
  const { data: jobResult, isLoading: resultLoading } = useQuery({
    queryKey: ["job-result", jobId],
    queryFn: () => jobsAPI.getJobResult(jobId).then(res => res.data),
    enabled: !!job && job.status === "done",
  })

  // Calculate regions with bounding box coordinates
  const regions = useMemo(() => {
    if (!jobResult?.regions) return []

    return jobResult.regions.map(region => ({
      ...region,
      page_number: jobResult.pages.find(p => p.id === region.page_id)?.page_number || 1,
      piiDetected: (region.pii_detected?.length || 0) > 0,
      trustScore: region.trust_score || 0,
    }))
  }, [jobResult])

  const totalPages = jobResult?.pages.length || 1

  // Filter regions by current page
  const currentPageRegions = regions.filter(region => region.page_number === currentPage)

  const handleRegionSelect = useCallback((regionId: string) => {
    setSelectedRegionId(regionId)
  }, [])

  const handleRegionEdit = useCallback((regionId: string) => {
    // TODO: Open edit modal or inline editor
    console.log("Edit region:", regionId)
  }, [])

  const handleDownloadRedactedPdf = async () => {
    if (!job?.redacted_path) {
      toast.error("Redacted PDF not available")
      return
    }

    try {
      const response = await jobsAPI.downloadRedactedPdf(jobId)
      const blob = new Blob([response.data], { type: "application/pdf" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `redacted_${job.original_filename}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      toast.success("Redacted PDF downloaded")
    } catch (error) {
      console.error("Download failed:", error)
      toast.error("Failed to download redacted PDF")
    }
  }

  const handleExportJSON = async () => {
    if (!jobResult) {
      toast.error("Job results not available")
      return
    }

    try {
      const jsonData = {
        job: jobResult.job,
        pages: jobResult.pages,
        regions: jobResult.regions,
        exported_at: new Date().toISOString()
      }

      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${job?.original_filename.replace('.pdf', '')}_extracted_data.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      toast.success("JSON data exported")
    } catch (error) {
      console.error("Export failed:", error)
      toast.error("Failed to export JSON")
    }
  }

  if (jobLoading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Job not found</h1>
          <p className="text-gray-600 mb-4">The job you're looking for doesn't exist.</p>
          <Link href="/dashboard">
            <Button>Back to Dashboard</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.back()}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>

              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {job.original_filename}
                </h1>
                <p className="text-sm text-gray-600">
                  Job ID: {job.id}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {job.status === "done" && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRedactions(!showRedactions)}
                  >
                    {showRedactions ? (
                      <>
                        <EyeOff className="w-4 h-4 mr-2" />
                        Hide Redactions
                      </>
                    ) : (
                      <>
                        <Eye className="w-4 h-4 mr-2" />
                        Show Redactions
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExportJSON}
                  >
                    <FileJson className="w-4 h-4 mr-2" />
                    Export JSON
                  </Button>

                  {job.redacted_path && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDownloadRedactedPdf}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download Redacted
                    </Button>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    Share
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Job Status Banner */}
        {job.status === "processing" && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-brand-50 border border-brand-200 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
              <div>
                <h3 className="font-medium text-brand-900">Processing document...</h3>
                <p className="text-sm text-brand-700">{job.progress || "Analyzing content with AI"}</p>
              </div>
            </div>
          </motion.div>
        )}

        {job.status === "failed" && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 text-danger" />
              <div>
                <h3 className="font-medium text-danger">Processing failed</h3>
                <p className="text-sm text-gray-700">{job.error_message || "An error occurred while processing this document"}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Main Content */}
        {job.status === "done" && jobResult && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* PDF Viewer - Left Side */}
            <div className="lg:col-span-2">
              <PDFViewer
                fileUrl={`#`} // Would be the actual PDF URL
                pageNumber={currentPage}
                onPageChange={setCurrentPage}
                totalPages={totalPages}
                regions={currentPageRegions}
                selectedRegionId={selectedRegionId}
                onRegionSelect={handleRegionSelect}
                showRedactions={showRedactions}
              />
            </div>

            {/* Field List - Right Side */}
            <div className="lg:col-span-1">
              <FieldList
                regions={regions}
                selectedRegionId={selectedRegionId}
                onRegionSelect={handleRegionSelect}
                onRegionEdit={handleRegionEdit}
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                trustScoreFilter={trustFilter}
                onTrustScoreFilterChange={setTrustFilter}
                className="sticky top-24"
              />
            </div>
          </div>
        )}

        {/* Audit Timeline */}
        {job.status === "done" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-8"
          >
            <div className="bg-white rounded-lg border border-gray-200 shadow-soft p-6">
              <div className="flex items-center gap-2 mb-4">
                <History className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-semibold text-gray-900">Activity Timeline</h3>
              </div>

              <div className="text-center text-gray-500 py-8">
                <p>No audit history available yet</p>
              </div>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  )
}
