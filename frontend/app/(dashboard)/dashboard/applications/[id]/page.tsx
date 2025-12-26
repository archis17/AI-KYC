'use client'

import { useEffect, useState, useMemo, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import api from '@/lib/api'
import { KYCApplication } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { usePolling } from '@/hooks/usePolling'
import { useToast } from '@/components/ui/toast'
import { X } from 'lucide-react'

interface FileWithType {
  file: File
  documentType: string
  id: string
  uploadStatus?: 'pending' | 'uploading' | 'success' | 'error'
  errorMessage?: string
}

export default function ApplicationDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { showToast } = useToast()
  const [selectedFiles, setSelectedFiles] = useState<FileWithType[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const fetchApplication = useCallback(async () => {
    const response = await api.get(`/api/kyc/applications/${params.id}`)
    return response.data as KYCApplication
  }, [params.id])

  // Poll for updates if application is processing
  const { data: application, loading, stopPolling, refetch } = usePolling(
    fetchApplication,
    {
      enabled: true,
      interval: 2500,
    }
  )

  // Stop polling when status is final
  useEffect(() => {
    if (application && !['processing', 'pending'].includes(application.status)) {
      stopPolling()
    }
  }, [application?.status, stopPolling])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    const newFiles: FileWithType[] = files.map((file) => ({
      file,
      documentType: 'id_card', // Default type
      id: Math.random().toString(36).substr(2, 9),
      uploadStatus: 'pending',
    }))

    setSelectedFiles((prev) => [...prev, ...newFiles])
    // Reset input
    e.target.value = ''
  }

  const removeFile = (id: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.id !== id))
    setUploadProgress((prev) => {
      const newProgress = { ...prev }
      delete newProgress[id]
      return newProgress
    })
  }

  const updateFileType = (id: string, documentType: string) => {
    setSelectedFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, documentType } : f))
    )
  }

  const handleBulkUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    const results: { success: number; failed: number } = { success: 0, failed: 0 }

    // Upload files sequentially
    for (const fileWithType of selectedFiles) {
      try {
        // Update status to uploading
        setSelectedFiles((prev) =>
          prev.map((f) =>
            f.id === fileWithType.id ? { ...f, uploadStatus: 'uploading' } : f
          )
        )

        const formData = new FormData()
        formData.append('file', fileWithType.file)
        formData.append('document_type', fileWithType.documentType)

        await api.post(
          `/api/kyc/applications/${params.id}/documents?document_type=${fileWithType.documentType}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const percentCompleted = Math.round(
                  (progressEvent.loaded * 100) / progressEvent.total
                )
                setUploadProgress((prev) => ({
                  ...prev,
                  [fileWithType.id]: percentCompleted,
                }))
              }
            },
          }
        )

        // Update status to success
        setSelectedFiles((prev) =>
          prev.map((f) =>
            f.id === fileWithType.id ? { ...f, uploadStatus: 'success' } : f
          )
        )
        results.success++
      } catch (error: any) {
        console.error('Upload failed:', error)
        const errorMessage = error.response?.data?.detail || 'Upload failed'
        setSelectedFiles((prev) =>
          prev.map((f) =>
            f.id === fileWithType.id
              ? { ...f, uploadStatus: 'error', errorMessage }
              : f
          )
        )
        results.failed++
      }
    }

    // Refetch application data
    await refetch()

    // Show results
    if (results.failed === 0) {
      showToast(`Successfully uploaded ${results.success} document(s)`, 'success')
      // Clear successful uploads after a delay
      setTimeout(() => {
        setSelectedFiles((prev) => prev.filter((f) => f.uploadStatus !== 'success'))
        setUploadProgress({})
      }, 2000)
    } else {
      showToast(
        `Uploaded ${results.success} document(s), ${results.failed} failed`,
        'error'
      )
    }

    setUploading(false)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
        <div className="h-64 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    )
  }

  if (!application) {
    return <div className="text-center py-12">Application not found</div>
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "success" | "warning"> = {
      approved: 'success',
      rejected: 'destructive',
      review: 'warning',
      processing: 'secondary',
      pending: 'default',
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  const getProcessingProgress = () => {
    if (!application?.processing_stage) return { percentage: 0, stages: [] }
    
    const stages = [
      { key: 'pending', label: 'Pending', percentage: 0 },
      { key: 'uploading', label: 'Uploading', percentage: 10 },
      { key: 'ocr', label: 'OCR Processing', percentage: 30 },
      { key: 'ner', label: 'Entity Extraction', percentage: 50 },
      { key: 'llm', label: 'AI Validation', percentage: 70 },
      { key: 'risk_scoring', label: 'Risk Scoring', percentage: 85 },
      { key: 'workflow', label: 'Workflow', percentage: 95 },
      { key: 'completed', label: 'Completed', percentage: 100 },
    ]

    const currentStageIndex = stages.findIndex(s => s.key === application.processing_stage)
    const currentPercentage = currentStageIndex >= 0 ? stages[currentStageIndex].percentage : 0

    return {
      percentage: currentPercentage,
      stages,
      currentStage: application.processing_stage,
    }
  }

  const progress = getProcessingProgress()

  if (loading && !application) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
        <div className="h-64 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    )
  }

  if (!application) {
    return <div className="text-center py-12">Application not found</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Application #{application.id}</h1>
          <p className="text-muted-foreground mt-2">
            Created {new Date(application.created_at).toLocaleDateString()}
          </p>
        </div>
        <motion.div
          key={application.status}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.2 }}
        >
          {getStatusBadge(application.status)}
        </motion.div>
      </div>

      {/* Processing Progress */}
      {(application.status === 'processing' || application.status === 'pending') && (
        <Card>
          <CardHeader>
            <CardTitle>Processing Status</CardTitle>
            <CardDescription>
              {application.processing_message || 'Processing your application...'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={progress.percentage} max={100} animated />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              {progress.stages.map((stage) => {
                const isActive = stage.key === progress.currentStage
                const isCompleted = progress.stages.findIndex(s => s.key === progress.currentStage) >
                  progress.stages.findIndex(s => s.key === stage.key)
                
                return (
                  <div
                    key={stage.key}
                    className={`p-2 rounded ${
                      isActive
                        ? 'bg-primary/10 border border-primary'
                        : isCompleted
                        ? 'bg-green-50 border border-green-200'
                        : 'bg-gray-50 border border-gray-200'
                    }`}
                  >
                    <div className="font-medium">{stage.label}</div>
                    <div className="text-xs text-muted-foreground">{stage.percentage}%</div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {application.risk_score && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Risk Score</CardTitle>
              <CardDescription>AI-generated risk assessment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Risk Score</span>
                    <span className="text-2xl font-bold">{application.risk_score.score.toFixed(1)}/100</span>
                  </div>
                  <Progress
                    value={application.risk_score.score}
                    max={100}
                    className={`h-2.5 ${
                      application.risk_score.score < 30
                        ? '[&>div]:bg-green-500'
                        : application.risk_score.score < 60
                        ? '[&>div]:bg-yellow-500'
                        : '[&>div]:bg-red-500'
                    }`}
                  />
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Decision: {application.risk_score.decision.toUpperCase()}</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-line">
                    {application.risk_score.reasoning}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Select multiple documents, assign types, then click upload
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Input
              type="file"
              accept="image/*,.pdf"
              multiple
              onChange={handleFileSelect}
              disabled={uploading}
              className="cursor-pointer"
            />
            <p className="text-xs text-muted-foreground mt-1">
              You can select multiple files at once
            </p>
          </div>

          {selectedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2"
            >
              <div className="text-sm font-medium">Selected Files ({selectedFiles.length})</div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                <AnimatePresence>
                  {selectedFiles.map((fileWithType) => (
                    <motion.div
                      key={fileWithType.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="flex items-center gap-2 p-3 border rounded-lg bg-gray-50"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {fileWithType.file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {(fileWithType.file.size / 1024).toFixed(1)} KB
                        </p>
                        {fileWithType.uploadStatus === 'uploading' && (
                          <div className="mt-2">
                            <Progress
                              value={uploadProgress[fileWithType.id] || 0}
                              max={100}
                              className="h-1"
                            />
                          </div>
                        )}
                        {fileWithType.uploadStatus === 'success' && (
                          <p className="text-xs text-green-600 mt-1">✓ Uploaded successfully</p>
                        )}
                        {fileWithType.uploadStatus === 'error' && (
                          <p className="text-xs text-red-600 mt-1">
                            ✗ {fileWithType.errorMessage || 'Upload failed'}
                          </p>
                        )}
                      </div>
                      <select
                        value={fileWithType.documentType}
                        onChange={(e) =>
                          updateFileType(fileWithType.id, e.target.value)
                        }
                        disabled={uploading || fileWithType.uploadStatus === 'uploading'}
                        className="h-8 rounded-md border border-input bg-background px-2 py-1 text-xs"
                      >
                        <option value="id_card">ID Card</option>
                        <option value="passport">Passport</option>
                        <option value="proof_of_address">Proof of Address</option>
                        <option value="bank_statement">Bank Statement</option>
                        <option value="other">Other</option>
                      </select>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(fileWithType.id)}
                        disabled={uploading || fileWithType.uploadStatus === 'uploading'}
                        className="h-8 w-8 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Button
                  onClick={handleBulkUpload}
                  disabled={uploading || selectedFiles.length === 0}
                  className="w-full"
                >
                  {uploading
                    ? `Uploading... (${selectedFiles.filter((f) => f.uploadStatus === 'uploading').length}/${selectedFiles.length})`
                    : `Upload ${selectedFiles.length} Document(s)`}
                </Button>
              </motion.div>
            </motion.div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documents ({application.documents?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {application.documents && application.documents.length > 0 ? (
            <div className="space-y-4">
              <AnimatePresence>
                {application.documents.map((doc, index) => (
                  <motion.div
                    key={doc.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className="border rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="font-medium">{doc.file_name}</p>
                        <p className="text-sm text-muted-foreground">{doc.document_type}</p>
                      </div>
                      {doc.ocr_confidence !== null && (
                        <Badge variant="secondary">
                          OCR: {(doc.ocr_confidence * 100).toFixed(1)}%
                        </Badge>
                      )}
                    </div>
                    {doc.extracted_entities && (
                      <div className="mt-2 text-sm space-y-1">
                        {doc.extracted_entities.name && (
                          <p><span className="font-medium">Name:</span> {doc.extracted_entities.name}</p>
                        )}
                        {doc.extracted_entities.dob && (
                          <p><span className="font-medium">DOB:</span> {doc.extracted_entities.dob}</p>
                        )}
                        {doc.extracted_entities.address && (
                          <p><span className="font-medium">Address:</span> {doc.extracted_entities.address}</p>
                        )}
                        {doc.extracted_entities.id_number && (
                          <p><span className="font-medium">ID:</span> {doc.extracted_entities.id_number}</p>
                        )}
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <p className="text-muted-foreground">No documents uploaded yet</p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

