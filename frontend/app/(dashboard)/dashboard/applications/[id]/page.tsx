'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import api from '@/lib/api'
import { KYCApplication } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

export default function ApplicationDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [application, setApplication] = useState<KYCApplication | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [documentType, setDocumentType] = useState('id_card')

  useEffect(() => {
    fetchApplication()
  }, [params.id])

  const fetchApplication = async () => {
    try {
      const response = await api.get(`/api/kyc/applications/${params.id}`)
      setApplication(response.data)
    } catch (error) {
      console.error('Failed to fetch application:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)

    try {
      await api.post(
        `/api/kyc/applications/${params.id}/documents?document_type=${documentType}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      await fetchApplication()
      alert('Document uploaded successfully')
    } catch (error: any) {
      console.error('Upload failed:', error)
      alert(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Application #{application.id}</h1>
          <p className="text-muted-foreground mt-2">
            Created {new Date(application.created_at).toLocaleDateString()}
          </p>
        </div>
        {getStatusBadge(application.status)}
      </div>

      {application.risk_score && (
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
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${
                      application.risk_score.score < 30
                        ? 'bg-green-500'
                        : application.risk_score.score < 60
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${application.risk_score.score}%` }}
                  />
                </div>
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
      )}

      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>Upload KYC documents for validation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Document Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="id_card">ID Card</option>
              <option value="passport">Passport</option>
              <option value="proof_of_address">Proof of Address</option>
              <option value="bank_statement">Bank Statement</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <Input
              type="file"
              accept="image/*,.pdf"
              onChange={handleFileUpload}
              disabled={uploading}
            />
            {uploading && <p className="text-sm text-muted-foreground mt-2">Uploading...</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documents ({application.documents?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {application.documents && application.documents.length > 0 ? (
            <div className="space-y-4">
              {application.documents.map((doc) => (
                <div key={doc.id} className="border rounded-lg p-4">
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
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No documents uploaded yet</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

