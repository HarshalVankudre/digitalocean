import React from 'react'

type Props = {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
}

export default function FormField({label, value, onChange, type='text', placeholder}: Props){
  return (
    <label className="block text-sm">
      <span className="text-slate-600">{label}</span>
      <input
        className="mt-1 w-full rounded-xl border-slate-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e)=>onChange(e.target.value)}
      />
    </label>
  )
}
