import { Outlet, useLocation } from "react-router-dom"
import Footer from "../../components/layout/Footer"
import Header from "../../components/layout/Header"

const Layout = () => {
    const { pathname } = useLocation();
    console.log(pathname);
    const isVentureDetail = /^\/ventures\/[a-zA-Z0-9-]+$/.test(pathname);

    return (
        <main>
            {!isVentureDetail && <Header />}
            <Outlet />
            {!isVentureDetail && <Footer />}
        </main>
    )
}

export default Layout