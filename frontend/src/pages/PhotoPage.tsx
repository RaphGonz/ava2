import { useSearchParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'

export default function PhotoPage() {
  const [searchParams] = useSearchParams()
  const photoUrl = searchParams.get('url')
  const navigate = useNavigate()

  if (!photoUrl) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500 text-sm">No photo URL provided.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Minimal header */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/80">
        <button
          onClick={() => navigate('/chat')}
          className="text-gray-300 hover:text-white text-sm transition-colors"
        >
          &larr; Back to chat
        </button>
        <span className="text-gray-400 text-xs">Photo from Ava</span>
      </div>

      {/* Photo display */}
      <div className="flex-1 flex items-center justify-center p-4">
        <img
          src={photoUrl}
          alt="Photo from Ava"
          className="max-w-full max-h-full rounded-lg object-contain"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none'
          }}
        />
      </div>

      <p className="text-gray-600 text-xs text-center pb-4">
        This link expires in 24 hours
      </p>
    </div>
  )
}
