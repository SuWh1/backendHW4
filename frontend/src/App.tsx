import { useState, useEffect } from 'react'
import axios from 'axios'

// Connect directly to the backend API on port 8000
const API_BASE = 'http://localhost:8000'

interface Item {
  id: number
  title: string
  description: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

interface FileUpload {
  id: number
  filename: string
  s3_url: string
  content_type: string
  file_size: number
  created_at: string
}

function App() {
  const [items, setItems] = useState<Item[]>([])
  const [uploads, setUploads] = useState<FileUpload[]>([])
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Form states
  const [newItem, setNewItem] = useState({ title: '', description: '' })
  const [editingItem, setEditingItem] = useState<Item | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    console.log('App component mounted, starting API calls...')
    console.log('API_BASE URL:', API_BASE)
    console.log('window.location.origin:', window.location.origin)
    fetchItems()
    fetchUploads()
    checkHealth()
  }, [])

  const fetchItems = async () => {
    try {
      console.log('Fetching items...')
      console.log('Making request to:', `${API_BASE}/items`)
      const response = await axios.get(`${API_BASE}/items`)
      console.log('Items fetched successfully:', response.data)
      setItems(response.data)
    } catch (error) {
      console.error('Error fetching items:', error)
      setError('Failed to fetch items')
    }
  }

  const fetchUploads = async () => {
    try {
      console.log('Fetching uploads...')
      const response = await axios.get(`${API_BASE}/files`)
      console.log('Uploads fetched successfully:', response.data)
      setUploads(response.data)
    } catch (error) {
      console.error('Error fetching uploads:', error)
      setError('Failed to fetch uploads')
    }
  }

  const checkHealth = async () => {
    try {
      console.log('Checking health...')
      const response = await axios.get(`${API_BASE}/health`)
      console.log('Health check successful:', response.data)
      setHealth(response.data)
    } catch (error) {
      console.error('Error checking health:', error)
      setError('Failed to check health')
    }
  }

  const createItem = async () => {
    if (!newItem.title) return
    setLoading(true)
    try {
      await axios.post(`${API_BASE}/items`, newItem)
      setNewItem({ title: '', description: '' })
      await fetchItems()
    } catch (error) {
      console.error('Error creating item:', error)
    }
    setLoading(false)
  }

  const updateItem = async (id: number, updates: Partial<Item>) => {
    setLoading(true)
    try {
      await axios.put(`${API_BASE}/items/${id}`, updates)
      await fetchItems()
      setEditingItem(null)
    } catch (error) {
      console.error('Error updating item:', error)
    }
    setLoading(false)
  }

  const deleteItem = async (id: number) => {
    setLoading(true)
    try {
      await axios.delete(`${API_BASE}/items/${id}`)
      await fetchItems()
    } catch (error) {
      console.error('Error deleting item:', error)
    }
    setLoading(false)
  }

  const uploadFile = async () => {
    if (!selectedFile) return
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      await axios.post(`${API_BASE}/upload`, formData)
      setSelectedFile(null)
      await fetchUploads()
    } catch (error) {
      console.error('Error uploading file:', error)
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">FastAPI Production Demo</h1>
        
        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            <p>{error}</p>
            <button 
              onClick={() => setError(null)}
              className="mt-2 text-sm underline"
            >
              Dismiss
            </button>
          </div>
        )}
        
        {/* Health Status */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded">
              <h3 className="font-medium text-green-800">Database</h3>
              <p className="text-green-600">{health?.database || 'Checking...'}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="font-medium text-blue-800">Redis</h3>
              <p className="text-blue-600">{health?.redis || 'Checking...'}</p>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <h3 className="font-medium text-purple-800">Celery</h3>
              <p className="text-purple-600">{health?.celery || 'Checking...'}</p>
            </div>
          </div>
          <button 
            onClick={checkHealth}
            className="mt-4 bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          >
            Refresh Health
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Items CRUD */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold mb-4">Items (CRUD Demo)</h2>
            
            {/* Create Item */}
            <div className="mb-6 p-4 bg-gray-50 rounded">
              <h3 className="font-medium mb-3">Create New Item</h3>
              <input
                type="text"
                placeholder="Title"
                value={newItem.title}
                onChange={(e) => setNewItem({...newItem, title: e.target.value})}
                className="w-full p-2 border rounded mb-2"
              />
              <textarea
                placeholder="Description"
                value={newItem.description}
                onChange={(e) => setNewItem({...newItem, description: e.target.value})}
                className="w-full p-2 border rounded mb-2"
                rows={2}
              />
              <button 
                onClick={createItem}
                disabled={loading || !newItem.title}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Item'}
              </button>
            </div>

            {/* Items List */}
            <div className="space-y-3">
              {items.map((item) => (
                <div key={item.id} className="border rounded p-3">
                  {editingItem?.id === item.id ? (
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={editingItem.title}
                        onChange={(e) => setEditingItem({...editingItem, title: e.target.value})}
                        className="w-full p-2 border rounded"
                      />
                      <textarea
                        value={editingItem.description}
                        onChange={(e) => setEditingItem({...editingItem, description: e.target.value})}
                        className="w-full p-2 border rounded"
                        rows={2}
                      />
                      <div className="flex gap-2">
                        <button 
                          onClick={() => updateItem(item.id, {
                            title: editingItem.title,
                            description: editingItem.description
                          })}
                          className="bg-green-500 text-white px-3 py-1 rounded text-sm"
                        >
                          Save
                        </button>
                        <button 
                          onClick={() => setEditingItem(null)}
                          className="bg-gray-500 text-white px-3 py-1 rounded text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <h4 className="font-medium">{item.title}</h4>
                      <p className="text-gray-600 text-sm">{item.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Created: {new Date(item.created_at).toLocaleString()}
                      </p>
                      <div className="flex gap-2 mt-2">
                        <button 
                          onClick={() => setEditingItem(item)}
                          className="bg-yellow-500 text-white px-3 py-1 rounded text-sm"
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => deleteItem(item.id)}
                          className="bg-red-500 text-white px-3 py-1 rounded text-sm"
                        >
                          Delete
                        </button>
                        <button 
                          onClick={() => updateItem(item.id, { is_active: !item.is_active })}
                          className={`px-3 py-1 rounded text-sm text-white ${
                            item.is_active ? 'bg-orange-500' : 'bg-green-500'
                          }`}
                        >
                          {item.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* File Upload */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold mb-4">File Upload (S3 Demo)</h2>
            
            {/* Upload Form */}
            <div className="mb-6 p-4 bg-gray-50 rounded">
              <h3 className="font-medium mb-3">Upload to S3</h3>
              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full p-2 border rounded mb-2"
              />
              <button 
                onClick={uploadFile}
                disabled={loading || !selectedFile}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
              >
                {loading ? 'Uploading...' : 'Upload File'}
              </button>
            </div>

            {/* Uploaded Files */}
            <div className="space-y-3">
              {uploads.map((upload) => (
                <div key={upload.id} className="border rounded p-3">
                  <h4 className="font-medium">{upload.filename}</h4>
                  <p className="text-sm text-gray-600">
                    Type: {upload.content_type} | Size: {upload.file_size} bytes
                  </p>
                  <p className="text-xs text-gray-500">
                    Uploaded: {new Date(upload.created_at).toLocaleString()}
                  </p>
                  <a 
                    href={upload.s3_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-block mt-2 bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                  >
                    View File
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App