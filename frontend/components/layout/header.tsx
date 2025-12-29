'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import api from '@/lib/api'
import { User } from '@/types'

export function Header() {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await api.get('/api/auth/me')
        setUser(response.data)
      } catch (error) {
        console.error('Failed to fetch user:', error)
      }
    }
    fetchUser()
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    router.push('/login')
  }

  const isActive = (path: string) => pathname === path

  return (
    <header className="border-b bg-white">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">KYC Validation System</h1>
          <div className="flex items-center gap-4">
            <nav className="flex items-center gap-4">
              <Link 
                href="/dashboard" 
                className={`text-sm font-medium hover:text-primary transition-colors ${
                  isActive('/dashboard') ? 'text-primary' : 'text-muted-foreground'
                }`}
              >
                Dashboard
              </Link>
              {user?.role === 'admin' && (
                <>
                  <Link 
                    href="/admin" 
                    className={`text-sm font-medium hover:text-primary transition-colors ${
                      isActive('/admin') ? 'text-primary' : 'text-muted-foreground'
                    }`}
                  >
                    Admin
                  </Link>
                  <Link 
                    href="/analytics" 
                    className={`text-sm font-medium hover:text-primary transition-colors ${
                      isActive('/analytics') ? 'text-primary' : 'text-muted-foreground'
                    }`}
                  >
                    Analytics
                  </Link>
                </>
              )}
            </nav>
            <Button variant="ghost" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

