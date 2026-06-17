'use client'

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
    LayoutDashboard,
    FileText,
    Search,
    ShieldAlert,
    Shield
} from 'lucide-react';
import styles from "./Sidebar.module.css"

const navItems = [
    {
        section: 'Monitor',
        items: [
            { label: 'Dashboard', href: '/', icon: LayoutDashboard },
            { label: 'Threats', href: '/threats', icon: ShieldAlert },
        ]
    },

    {
        section: 'Analyze',
        items: [
            { label: 'Log Analysis', href: '/logs', icon: FileText },
            { label: 'Query', href: '/query', icon: Search },
        ]
    }
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className={styles.sidebar}> 
            <div className={styles.logo}>
                <div className={styles.logoMark}>
                    <Shield size={16} color="white" strokeWidth={2.5} />
                </div>
                <span className={styles.logoText}>SentinelAI</span>
            </div>

            <nav className={styles.nav}>
                {navItems.map((section) => (
                    <div key={section.section} className={styles.navSection}>
                        <p className={styles.navSectionLabel}>{section.section}</p>
                        {section.items.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname === item.href;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
                                >
                                    <Icon size={16} className={styles.navIcon} />
                                    {item.label}
                                </Link>
                            )
                        })}
                    </div>
                ))}
            </nav>

            <div className={styles.footer}>
                <span className={styles.statusDot} />
                <span className={styles.statusText}>All systems operational</span>
            </div>
        </aside>
    )
}