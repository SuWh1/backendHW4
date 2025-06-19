import React, { useState, useEffect } from 'react'
import VoiceComm from './components/VoiceComm'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState<'voice' | 'items'>('voice')

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-white">🎙️ A2A Communication System</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setActiveTab('voice')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'voice' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                🎙️ Voice Communication
              </button>
              <button
                onClick={() => setActiveTab('items')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'items' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                📋 Items & Files
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {activeTab === 'voice' ? (
        <VoiceComm />
      ) : (
        <ItemsInterface />
      )}
    </div>
  )
}

// Full Items CRUD Interface
const ItemsInterface: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [newItem, setNewItem] = useState({ title: '', description: '' })
  const [editingItem, setEditingItem] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const API_BASE = 'http://localhost:8000'

  // Fetch items
  const fetchItems = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/items/`)
      if (response.ok) {
        const data = await response.json()
        setItems(data)
      } else {
        setError('Failed to fetch items')
      }
    } catch (error) {
      console.error('Error fetching items:', error)
      setError('Error fetching items')
    } finally {
      setLoading(false)
    }
  }

  // Create item
  const createItem = async () => {
    if (!newItem.title.trim()) return

    try {
      const response = await fetch(`${API_BASE}/items/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newItem),
      })

      if (response.ok) {
        const data = await response.json()
        setItems(prev => [...prev, data])
        setNewItem({ title: '', description: '' })
        setError('')
      } else {
        setError('Failed to create item')
      }
    } catch (error) {
      console.error('Error creating item:', error)
      setError('Error creating item')
    }
  }

  // Update item
  const updateItem = async (id: number, updates: any) => {
    try {
      const response = await fetch(`${API_BASE}/items/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      })

      if (response.ok) {
        const data = await response.json()
        setItems(prev => prev.map(item => item.id === id ? data : item))
        setEditingItem(null)
        setError('')
      } else {
        setError('Failed to update item')
      }
    } catch (error) {
      console.error('Error updating item:', error)
      setError('Error updating item')
    }
  }

  // Delete item
  const deleteItem = async (id: number) => {
    try {
      const response = await fetch(`${API_BASE}/items/${id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setItems(prev => prev.filter(item => item.id !== id))
        setError('')
      } else {
        setError('Failed to delete item')
      }
    } catch (error) {
      console.error('Error deleting item:', error)
      setError('Error deleting item')
    }
  }

  // Upload file
  const uploadFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE}/upload/`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        setFiles(prev => [...prev, data])
        fetchFiles() // Refresh the list
        setError('')
      } else {
        setError('Failed to upload file')
      }
    } catch (error) {
      console.error('Error uploading file:', error)
      setError('Error uploading file')
    }
  }

  // Fetch files
  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_BASE}/files/`)
      if (response.ok) {
        const data = await response.json()
        setFiles(data)
      }
    } catch (error) {
      console.error('Error fetching files:', error)
    }
  }

  // Load data on mount
  useEffect(() => {
    fetchItems()
    fetchFiles()
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        
        {/* Error Display */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-6">
            <p>{error}</p>
            <button 
              onClick={() => setError('')}
              className="mt-2 text-sm underline"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Items CRUD Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4">📋 Items Management</h2>
            
            {/* Create Item Form */}
            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
              <h3 className="text-lg font-semibold mb-3">Create New Item</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Item title"
                  value={newItem.title}
                  onChange={(e) => setNewItem(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full p-3 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
                />
                <textarea
                  placeholder="Item description"
                  value={newItem.description}
                  onChange={(e) => setNewItem(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full p-3 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none h-24"
                />
                <button
                  onClick={createItem}
                  className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-semibold transition-colors"
                >
                  Create Item
                </button>
              </div>
            </div>

            {/* Items List */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Items ({items.length})</h3>
                <button
                  onClick={fetchItems}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded transition-colors"
                >
                  {loading ? 'Loading...' : 'Refresh'}
                </button>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {items.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">No items found. Create your first item above!</p>
                ) : (
                  items.map((item) => (
                    <div key={item.id} className="p-4 bg-gray-700 rounded-lg">
                      {editingItem?.id === item.id ? (
                        // Edit mode
                        <div className="space-y-3">
                          <input
                            type="text"
                            value={editingItem.title}
                            onChange={(e) => setEditingItem({...editingItem, title: e.target.value})}
                            className="w-full p-2 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
                          />
                          <textarea
                            value={editingItem.description}
                            onChange={(e) => setEditingItem({...editingItem, description: e.target.value})}
                            className="w-full p-2 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
                            rows={2}
                          />
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => updateItem(item.id, {
                                title: editingItem.title,
                                description: editingItem.description
                              })}
                              className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm transition-colors"
                            >
                              Save
                            </button>
                            <button 
                              onClick={() => setEditingItem(null)}
                              className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        // View mode
                        <div>
                          <h4 className="font-semibold text-blue-300">{item.title}</h4>
                          <p className="text-gray-300 mt-1">{item.description}</p>
                          <p className="text-gray-500 text-sm mt-2">
                            Created: {new Date(item.created_at).toLocaleString()}
                          </p>
                          <div className="flex space-x-2 mt-3">
                            <button 
                              onClick={() => setEditingItem(item)}
                              className="bg-yellow-600 hover:bg-yellow-700 px-3 py-1 rounded text-sm transition-colors"
                            >
                              Edit
                            </button>
                            <button 
                              onClick={() => deleteItem(item.id)}
                              className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm transition-colors"
                            >
                              Delete
                            </button>
                            <button 
                              onClick={() => updateItem(item.id, { is_active: !item.is_active })}
                              className={`px-3 py-1 rounded text-sm transition-colors ${
                                item.is_active 
                                  ? 'bg-orange-600 hover:bg-orange-700' 
                                  : 'bg-green-600 hover:bg-green-700'
                              }`}
                            >
                              {item.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* File Upload Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4">📁 File Management</h2>
            
            {/* File Upload */}
            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
              <h3 className="text-lg font-semibold mb-3">Upload File to S3</h3>
              <input
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) uploadFile(file)
                }}
                className="w-full p-3 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
              />
              <p className="text-sm text-gray-400 mt-2">
                Select a file to upload to AWS S3. Background processing will handle the upload.
              </p>
            </div>

            {/* Files List */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Uploaded Files ({files.length})</h3>
                <button
                  onClick={fetchFiles}
                  className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition-colors"
                >
                  Refresh
                </button>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {files.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">No files uploaded yet. Upload a file above!</p>
                ) : (
                  files.map((file) => (
                    <div key={file.id} className="p-4 bg-gray-700 rounded-lg">
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="font-semibold text-blue-300">{file.filename}</h4>
                          <p className="text-gray-300 text-sm">
                            Size: {(file.file_size / 1024).toFixed(2)} KB | 
                            Type: {file.content_type}
                          </p>
                          <p className="text-gray-500 text-sm">
                            Uploaded: {new Date(file.created_at).toLocaleString()}
                          </p>
                        </div>
                        <a
                          href={file.s3_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition-colors"
                        >
                          View File
                        </a>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">🏥 System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <HealthCheck endpoint="/health" label="API" />
            <HealthCheck endpoint="/health/redis" label="Redis" />
            <HealthCheck endpoint="/health/openai" label="OpenAI" />
            <DatabaseStatus />
          </div>
        </div>
      </div>
    </div>
  )
}

// Health Check Component
const HealthCheck: React.FC<{ endpoint: string; label: string }> = ({ endpoint, label }) => {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'unhealthy'>('checking')

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`http://localhost:8000${endpoint}`)
        setStatus(response.ok ? 'healthy' : 'unhealthy')
      } catch {
        setStatus('unhealthy')
      }
    }
    checkHealth()
  }, [endpoint])

  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'bg-green-600'
      case 'unhealthy': return 'bg-red-600'
      default: return 'bg-yellow-600'
    }
  }

  return (
    <div className={`p-4 rounded-lg ${getStatusColor()}`}>
      <h3 className="font-semibold">{label}</h3>
      <p className="text-sm">{status}</p>
    </div>
  )
}

// Database Status Component
const DatabaseStatus: React.FC = () => {
  return (
    <div className="p-4 rounded-lg bg-blue-600">
      <h3 className="font-semibold">Database</h3>
      <p className="text-sm">PostgreSQL + A2A Tables</p>
    </div>
  )
}

export default App