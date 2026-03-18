"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
    const router = useRouter();
    
    useEffect(() => {
        router.push('/dashboard');
    }, [router]);

    return (
        <div className="flex items-center justify-center min-h-screen bg-slate-50">
            <div className="animate-pulse text-indigo-600 font-bold text-xl">
                Loading Patient Portal...
            </div>
        </div>
    );
}
