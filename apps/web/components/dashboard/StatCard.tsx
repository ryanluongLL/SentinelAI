import { ReactNode } from "react";
import TiltedCard from "../bits/TiltedCard";
import CountUp from "../bits/CountUp";
import styles from "./StatCard.module.css"

type Accent = 'red' | 'green' | 'amber' | 'blue';

interface StatCardProps{
    label: string;
    value: number;
    icon: ReactNode;
    accent: Accent;
    delta?: number;
    deltaLabel?: string;
    suffix?: string;
}

const accentMap: Record<Accent, string> = {
    red: styles.accentRed,
    green: styles.accentGreen,
    amber: styles.accentAmber,
    blue: styles.accentBlue,
}

const accentIconMap: Record<Accent, string> = {
    red: styles.accentRedIcon,
    green: styles.accentGreenIcon,
    amber: styles.accentAmberIcon,
    blue: styles.accentBlueIcon,
}

export default function StatCard({
    label,
    value,
    icon,
    accent,
    delta,
    deltaLabel,
    suffix,
}: StatCardProps) {
    return (
        <TiltedCard className={styles.card}>
            <div className={styles.top}>
                <span className={styles.label}>{label}</span>
                <div className={`${styles.iconWrapper} ${accentMap[accent]}`}>
                    <span className={accentIconMap[accent]}>{icon}</span>
                </div>
            </div>
            <div className={styles.value}>
                <CountUp to={value} duration={1000} suffix={suffix ?? ''} />
            </div>
            {delta !== undefined && (
                <div className={styles.footer}>
                    <span className={`${styles.delta} ${delta > 0 ? styles.deltaUp : styles.deltaDown}`}>
                        {delta > 0 ? '+' : ''}{delta}
                    </span>
                    <span className={styles.footerLabel}>{deltaLabel}</span>
                </div>
            )}
        </TiltedCard>
    )
}