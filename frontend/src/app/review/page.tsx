"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Keyboard, Check, X, SkipForward, RotateCcw, Search } from "lucide-react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { TrustScoreBadge } from "@/components/ui/trust-score-badge"
import { reviewAPI, ReviewQueueItem, ReviewSubmission } from "@/lib/api"
import { useAuthStore } from "@/stores/auth"
import { toast } from "sonner"

interface ReviewItemWithIndex extends ReviewQueueItem {
  index: number
}

export default function ReviewPage() {
  const { user } = useAuthStore()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [searchTerm, setSearchTerm] = useState("")
  const [verifiedValue, setVerifiedValue] = useState("")
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)

  const { data: items, isLoading, refetch } = useQuery({
    queryKey: ["review-queue", searchTerm],
    queryFn: () => reviewAPI.getReviewQueue({ limit: 50 }).then(res => res.data),
  })

  const approveMutation = useMutation({
    mutationFn: ({ itemId, action, value }: { itemId: string; action: string; value?: string }) =>
      reviewAPI.reviewRegion(itemId, { verified_value: value, action: action as any }),
    onSuccess: () => {
      toast.success("Field approved")
      moveToNext()
    },
    onError: (error) => {
      console.error("Review failed:", error)
      toast.error("Failed to save review")
    }
  })

  const reviewItems: ReviewItemWithIndex[] = items?.map((item, index) => ({ ...item, index })) || []
  const currentItem = reviewItems[currentIndex]

  const moveToNext = useCallback(() => {
    if (currentIndex < reviewItems.length - 1) {
      setCurrentIndex(prev => prev + 1)
      setVerifiedValue("")
    } else {
      toast.info("Review queue completed!")
      refetch()
      setCurrentIndex(0)
    }
  }, [currentIndex, reviewItems.length, refetch])

  const handleApprove = useCallback(() => {
    if (!currentItem) return
    approveMutation.mutate({
      itemId: currentItem.region_id,
      action: "approve"
    })
  }, [currentItem, approveMutation])

  const handleCorrect = useCallback(() => {
    if (!currentItem || !verifiedValue.trim()) {
      toast.error("Please enter a corrected value")
      return
    }
    approveMutation.mutate({
      itemId: currentItem.region_id,
      action: "correct",
      value: verifiedValue
    })
  }, [currentItem, verifiedValue, approveMutation])

  const handleSkip = useCallback(() => {
    if (!currentItem) return
    approveMutation.mutate({
      itemId: currentItem.region_id,
      action: "skip"
    })
  }, [currentItem, approveMutation])

  const handleUndo = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1)
    }
  }, [currentIndex])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!currentItem) return

      // Ignore when typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (e.key) {
        case "j":
        case "ArrowDown":
          e.preventDefault()
          moveToNext()
          break
        case "k":
        case "ArrowUp":
          e.preventDefault()
          if (currentIndex > 0) {
            setCurrentIndex(prev => prev - 1)
          }
          break
        case "e":
          e.preventDefault()
          document.getElementById("edit-input")?.focus()
          break
        case "Enter":
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            handleCorrect()
          } else {
            e.preventDefault()
            handleApprove()
          }
          break
        case "Escape":
          e.preventDefault()
          handleSkip()
          break
        case "u":
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            handleUndo()
          }
          break
        case "?":
          if (e.shiftKey) {
            e.preventDefault()
            setShowKeyboardHelp(!showKeyboardHelp)
          }
          break
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [currentItem, currentIndex, moveToNext, handleApprove, handleCorrect, handleSkip, handleUndo, showKeyboardHelp])

  if (!user || user.role !== "reviewer" && user.role !== "admin") {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access the review queue.</p>
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
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-semibold text-brand-900">Review Queue</h1>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>{currentIndex + 1}</span>
                <span>/</span>
                <span>{reviewItems.length}</span>
                {reviewItems.length === 0 && <span className="text-warning">No items to review</span>}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search fields..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent"
                />
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowKeyboardHelp(!showKeyboardHelp)}
              >
                <Keyboard className="w-4 h-4 mr-2" />
                Shortcuts
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center" style={{ height: '400px' }}>
            <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : reviewItems.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-success" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">All caught up!</h2>
            <p className="text-gray-600">No items in the review queue.</p>
          </div>
        ) : currentItem ? (
          <motion.div
            key={currentItem.region_id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
          >
            {/* Context Preview */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-soft p-6">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Context Preview</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Document: {currentItem.job_filename}</div>
                  <div>Page: {currentItem.page_number}</div>
                  <div>Label: {currentItem.label}</div>
                </div>
              </div>

              {/* Bounding Box Visualization */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 bg-gray-50">
                <div className="text-center text-sm text-gray-600 mb-2">
                  Bounding Box Preview
                </div>
                <div
                  className="border-2 border-brand-400 bg-brand-50 rounded mx-auto"
                  style={{
                    width: `${(currentItem.bbox.x2 - currentItem.bbox.x1) * 0.5}px`,
                    height: `${(currentItem.bbox.y2 - currentItem.bbox.y1) * 0.5}px`
                  }}
                >
                  <div className="w-full h-full flex items-center justify-center text-xs text-brand-700">
                    Region Area
                  </div>
                </div>
              </div>
            </div>

            {/* Review Interface */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-soft p-6">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Review Field</h3>
                  {currentItem.trust_score && (
                    <TrustScoreBadge score={currentItem.trust_score} />
                  )}
                </div>

                {/* Original Text */}
                {currentItem.raw_text && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Original Text:</label>
                    <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm">
                      {currentItem.raw_text}
                    </div>
                  </div>
                )}

                {/* Normalized Text */}
                {currentItem.normalized_text && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Extracted Text:
                    </label>
                    <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm">
                      {currentItem.normalized_text}
                    </div>
                  </div>
                )}

                {/* PII Detection */}
                {currentItem.pii_detected && currentItem.pii_detected.length > 0 && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">PII Detected:</label>
                    <div className="flex flex-wrap gap-2">
                      {currentItem.pii_detected.map((pii, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-danger/10 text-danger text-xs rounded-full border border-danger/20"
                        >
                          {pii.entity} ({(pii.confidence * 100).toFixed(0)}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Edit Input */}
                <div className="mb-6">
                  <label htmlFor="edit-input" className="block text-sm font-medium text-gray-700 mb-2">
                    Corrected Value (Press <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">E</kbd> to focus):
                  </label>
                  <textarea
                    id="edit-input"
                    value={verifiedValue}
                    onChange={(e) => setVerifiedValue(e.target.value)}
                    placeholder="Enter corrected value..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent"
                    rows={3}
                  />
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-3 gap-3">
                  <Button
                    variant="outline"
                    onClick={handleSkip}
                    className="flex items-center justify-center"
                  >
                    <SkipForward className="w-4 h-4 mr-2" />
                    Skip
                    <kbd className="ml-auto text-xs bg-gray-100 px-1 py-0.5 rounded">Esc</kbd>
                  </Button>

                  <Button
                    onClick={handleApprove}
                    className="flex items-center justify-center bg-success hover:bg-success/90"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                    <kbd className="ml-auto text-xs bg-white/20 px-1 py-0.5 rounded">Enter</kbd>
                  </Button>

                  <Button
                    onClick={handleCorrect}
                    disabled={!verifiedValue.trim()}
                    className="flex items-center justify-center bg-brand-600 hover:bg-brand-700"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Correct
                    <kbd className="ml-auto text-xs bg-white/20 px-1 py-0.5 rounded">⌘Enter</kbd>
                  </Button>
                </div>

                {/* Navigation */}
                <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleUndo}
                    disabled={currentIndex === 0}
                  >
                    Previous
                    <kbd className="ml-1 text-xs bg-gray-100 px-1 py-0.5 rounded">K</kbd>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={moveToNext}
                    disabled={currentIndex === reviewItems.length - 1}
                  >
                    Next
                    <kbd className="ml-1 text-xs bg-gray-100 px-1 py-0.5 rounded">J</kbd>
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        ) : null}
      </main>

      {/* Keyboard Help Modal */}
      <AnimatePresence>
        {showKeyboardHelp && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowKeyboardHelp(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Keyboard Shortcuts</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Focus edit field</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">E</kbd>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Approve field</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Enter</kbd>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Save & next</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">⌘Enter</kbd>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Skip field</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Esc</kbd>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Previous field</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">K / ↑</kbd>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Next field</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">J / ↓</kbd>
                </div>
              </div>
              <Button
                className="mt-4 w-full"
                onClick={() => setShowKeyboardHelp(false)}
              >
                Close
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}