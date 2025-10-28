import React from 'react'
import ReactMarkdown from 'react-markdown'

type Props = { role: 'user'|'assistant'; content: string }

export default function ChatMessage({role, content}: Props){
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} my-2`}>
      <div className={`prose max-w-[70ch] rounded-2xl px-4 py-3 shadow ${isUser ? 'bg-indigo-600 text-white' : 'bg-white'} `}>
        {isUser ? <div>{content}</div> : <ReactMarkdown>{content}</ReactMarkdown>}
      </div>
    </div>
  )
}
