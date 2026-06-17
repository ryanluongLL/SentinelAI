"use client";

import { useRef, MouseEvent, ReactNode } from "react";

interface TiltedCardProps{
    children: ReactNode;
    className?: string;
    maxTilt?: number;
    scale?: number;
}

export default function TiltedCard({
    children,
    className,
    maxTilt = 6,
    scale = 1.01,
}: TiltedCardProps) {
    const cardRef = useRef<HTMLDivElement>(null);

    const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
        const card = cardRef.current;
        if (!card) return;
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -maxTilt;
        const rotateY = ((x - centerX) / centerX) * maxTilt;
        card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`;
    }

    const handleMouseLeave = () => {
        const card = cardRef.current;
        if (!card) return;
        card.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg) scale(1)';
    }

    return (
        <div
            ref={cardRef}
            className={className}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            style={{transition: 'transform 200ms ease', willChange: 'transform'}}
        >
            {children}
        </div>
    )
}