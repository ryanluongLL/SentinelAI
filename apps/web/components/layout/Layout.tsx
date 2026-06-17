import Sidebar from "./Sidebar";
import Header from "./Header";
import styles from "./Layout.module.css"

export default function Layout({ children }: { children: React.ReactNode }) {
    return (
        <div className={styles.shell}>
            <Sidebar />
            <div className={styles.main}>
                <Header />
                <main className={styles.content}>
                    {children}
                </main>
            </div>
        </div>
    )
}