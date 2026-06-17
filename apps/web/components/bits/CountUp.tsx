"use client";

import { useState, useEffect, useRef } from "react";

interface CountUpProps{
    to: number;
    duration?: number;
    decimals?: number;
    prefix?: string;
    suffix?: string;
    className?: string;
}

export default function CountUp({
    to,
    duration = 1200,
    decimals = 0,
    prefix = '',
    suffix = '',
    className,
}: CountUpProps) {
    const [value, setValue] = useState(0);
    const startTime = useRef<number | null>(null);
    const frameRef = useRef<number>(0);

    useEffect(() => {
        const animate = (timestamp: number) => {
            if (!startTime.current) startTime.current = timestamp;
            const elapsed = timestamp - startTime.current;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setValue(parseFloat((eased * to).toFixed(decimals)))
            if (progress < 1) {
                frameRef.current = requestAnimationFrame(animate);
            }
        };
        frameRef.current = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(frameRef.current);
    }, [to, duration, decimals]);

    return (
        <span className={className}>
            {prefix}{value.toLocaleString()}{suffix}
        </span>
    )
}