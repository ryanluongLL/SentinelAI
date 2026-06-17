"use client"

import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import styles from "./Header.module.css"

const pageTitles: Record<string, string> = {
    '/': 'Dashboard',
    '/threats': 'Threats',
    '/logs': 'Log Analysis',
    '/query': 'Natural Language Query',
}

export default function Header() {
    const pathname = usePathname();
    const [time, setTime] = useState('');

    useEffect(() => {
        const update = () => {
            setTime(new Date().toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            }))
        }
        update();
        const interval = setInterval(update, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <header className={styles.header}>
            <h1 className={styles.title}>{pageTitles[pathname] ?? 'SentinelAI'}</h1>
            <div className={styles.badge}>
                <span className={styles.liveDot} />
                Live
            </div>
            <span className={styles.time}>{time}</span>
        </header>
    )
}