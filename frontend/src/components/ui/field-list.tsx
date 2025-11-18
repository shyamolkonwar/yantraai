"use client"

import { useState, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Filter, Edit3, CheckCircle, AlertTriangle, Shield, Eye } from "lucide-react"
import { Button } from "./button"
import { TrustScoreBadge } from "./trust-score-badge"
import { Region } from "@/lib/api"
import { cn, formatDate } from "@/lib/utils"

interface FieldListProps {
  regions: Region[]
  selectedRegionId?: string
  onRegionSelect: (regionId: string) => void
  onRegionEdit?: (regionId: string) => void
  searchTerm: string
  onSearchChange: (term: string) => void
  trustScoreFilter?: "all" | "high" | "medium" | "low"
  onTrustScoreFilterChange: (filter: "all" | "high" | "medium" | "low") => void
  className?: string
}

export function FieldList({
  regions,
  selectedRegionId,
  onRegionSelect,
  onRegionEdit,
  searchTerm,
  onSearchChange,
  trustScoreFilter,
  onTrustScoreFilterChange,
  className
}: FieldListProps) {
  const [isFilterOpen, setIsFilterOpen] = useState(false)

  const filteredRegions = useMemo(() => {
    let filtered = regions

    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase()
      filtered = filtered.filter(region =>
        region.label.toLowerCase().includes(searchLower) ||
        region.raw_text?.toLowerCase().includes(searchLower) ||
        region.normalized_text?.toLowerCase().includes(searchLower)
      )
    }

    // Filter by trust score
    if (trustScoreFilter !== "all") {
      filtered = filtered.filter(region => {
        if (!region.trust_score) return false
        if (trustScoreFilter === "high") return region.trust_score >= 0.8
        if (trustScoreFilter === "medium") return region.trust_score >= 0.5 && region.trust_score < 0.8
        if (trustScoreFilter === "low") return region.trust_score < 0.5
        return true
      })
    }

    return filtered
  }, [regions, searchTerm, trustScoreFilter])

  const getTrustScoreStats = () => {
    const stats = {
      total: regions.length,
      high: regions.filter(r => r.trust_score && r.trust_score >= 0.8).length,
      medium: regions.filter(r => r.trust_score && r.trust_score >= 0.5 && r.trust_score < 0.8).length,
      low: regions.filter(r => r.trust_score && r.trust_score < 0.5).length,
    }
    return stats
  }

  const stats = getTrustScoreStats()

  const getFieldIcon = (label: string) => {
    const lower = label.toLowerCase()
    if (lower.includes("table")) return <div className="w-4 h-4 bg-gray-200 rounded" />
    if (lower.includes("header")) return <div className="w-4 h-4 bg-blue-200 rounded" />
    if (lower.includes("signature")) return <div className="w-4 h-4 bg-green-200 rounded" />
    return <div className="w-4 h-4 bg-gray-100 rounded" />
  }

  return (
    <div className={cn("bg-white rounded-lg border border-gray-200 shadow-soft", className)}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Extracted Fields</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFilterOpen(!isFilterOpen)}
            className="relative"
          >
            <Filter className="w-4 h-4" />
            {trustScoreFilter !== "all" && (
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-brand-600 rounded-full" />
            )}
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search fields..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent"
          />
        </div>

        {/* Trust Score Stats */}
        <div className="flex items-center gap-4 mt-4 text-sm">
          <span className="text-gray-600">Total: {stats.total}</span>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-success rounded-full" />
            <span className="text-gray-600">High: {stats.high}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-warning rounded-full" />
            <span className="text-gray-600">Medium: {stats.medium}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-danger rounded-full" />
            <span className="text-gray-600">Low: {stats.low}</span>
          </div>
        </div>

        {/* Filter Dropdown */}
        <AnimatePresence>
          {isFilterOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="mt-4 pt-4 border-t border-gray-200"
            >
              <div className="space-y-2">
                <span className="text-sm font-medium text-gray-700">Filter by trust score:</span>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { value: "all", label: "All" },
                    { value: "high", label: "High (≥0.8)" },
                    { value: "medium", label: "Medium (0.5-0.8)" },
                    { value: "low", label: "Low (<0.5)" }
                  ].map(({ value, label }) => (
                    <Button
                      key={value}
                      variant={trustScoreFilter === value ? "default" : "outline"}
                      size="sm"
                      onClick={() => onTrustScoreFilterChange(value as any)}
                      className="justify-start text-xs"
                    >
                      {label}
                    </Button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Field List */}
      <div className="max-h-96 overflow-y-auto">
        {filteredRegions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No fields found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredRegions.map((region, index) => (
              <motion.div
                key={region.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                className={cn(
                  "p-4 cursor-pointer transition-all duration-200",
                  "hover:bg-gray-50",
                  selectedRegionId === region.id && "bg-brand-50 border-l-4 border-l-brand-600"
                )}
                onClick={() => onRegionSelect(region.id)}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Field Icon and Info */}
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="flex-shrink-0 mt-1">
                      {getFieldIcon(region.label)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-gray-900 capitalize">
                          {region.label}
                        </span>
                        {region.human_verified && (
                          <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />
                        )}
                        {region.pii_detected && region.pii_detected.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-danger">
                            <Shield className="w-3 h-3" />
                            <span>PII</span>
                          </div>
                        )}
                      </div>

                      {/* Normalized Text */}
                      {region.normalized_text && (
                        <p className="text-sm text-gray-900 mb-1 line-clamp-2">
                          {region.normalized_text}
                        </p>
                      )}

                      {/* Raw Text */}
                      {region.raw_text && region.raw_text !== region.normalized_text && (
                        <p className="text-xs text-gray-500 line-clamp-1">
                          Original: {region.raw_text}
                        </p>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Page {region.page_number || 1}</span>
                        {region.created_at && (
                          <span>{formatDate(region.created_at)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Trust Score and Actions */}
                  <div className="flex flex-col items-end gap-2">
                    {region.trust_score && (
                      <TrustScoreBadge
                        score={region.trust_score}
                        size="sm"
                        showTooltip={false}
                      />
                    )}

                    <div className="flex items-center gap-1">
                      {region.trust_score && region.trust_score < 0.6 && (
                        <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0" />
                      )}

                      {onRegionEdit && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            onRegionEdit(region.id)
                          }}
                        >
                          <Edit3 className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Verified Value (if different) */}
                {region.human_verified && region.verified_value && region.verified_value !== region.normalized_text && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="text-xs font-medium text-success mb-1">Verified value:</div>
                    <p className="text-sm text-gray-900">{region.verified_value}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
