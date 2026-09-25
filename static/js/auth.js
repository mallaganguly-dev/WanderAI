import { initializeApp } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-app.js";
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.3.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyAfbK6Inq9Jsrs9Spp3M7vySdWNkdALWc0",
    authDomain: "wanderai-f84d2.firebaseapp.com",
    projectId: "wanderai-f84d2",
    storageBucket: "wanderai-f84d2.firebasestorage.app",
    messagingSenderId: "455628284395",
    appId: "1:455628284395:web:5ce9ff829eab8a092479ae",
    measurementId: "G-WEYC7SK7Y2"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

console.log("Firebase Auth loaded successfully");


window.signupUser = async function () {

    console.log("signupUser() clicked");

    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value.trim();
    const message = document.getElementById("authMessage");

    message.textContent = "Creating account...";

    try {

        await createUserWithEmailAndPassword(
            auth,
            email,
            password
        );

        message.textContent = "Account created successfully!";

        setTimeout(() => {
            window.location.href = "/";
        }, 1000);

    } catch (error) {

        console.error("SIGNUP ERROR:", error);

        message.textContent = error.message;
    }
};


window.loginUser = async function () {

    console.log("loginUser() clicked");

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value.trim();
    const message = document.getElementById("authMessage");

    message.textContent = "Logging in...";

    try {

        await signInWithEmailAndPassword(
            auth,
            email,
            password
        );

        message.textContent = "Login successful!";

        setTimeout(() => {
            window.location.href = "/";
        }, 1000);

    } catch (error) {

        console.error("LOGIN ERROR:", error);

        message.textContent = error.message;
    }
};


window.googleLogin = async function () {

    console.log("googleLogin() clicked");

    const message = document.getElementById("authMessage");

    message.textContent = "Opening Google login...";

    try {

        const provider = new GoogleAuthProvider();

        await signInWithPopup(
            auth,
            provider
        );

        message.textContent = "Google login successful!";

        setTimeout(() => {
            window.location.href = "/";
        }, 1000);

    } catch (error) {

        console.error("GOOGLE LOGIN ERROR:", error);

        message.textContent = error.message;
    }
};
/* =========================
   DISPLAY GOOGLE PROFILE
   ========================= */

onAuthStateChanged(auth, (user) => {

    const profileArea =
        document.getElementById("profileArea");

    const profileImage =
        document.getElementById("profileImage");

    const loggedOutButtons =
        document.getElementById("loggedOutButtons");

    // These elements only exist on the homepage
    if (!profileArea || !profileImage || !loggedOutButtons) {
        return;
    }

    if (user) {

        console.log("Logged in user:", user);

        // Show Google profile picture
        if (user.photoURL) {

            profileImage.src = user.photoURL;

        } else {

            // Fallback if no profile picture exists
            profileImage.src =
                "https://ui-avatars.com/api/?name=" +
                encodeURIComponent(user.displayName || "User");
        }

        profileArea.style.display = "flex";
        loggedOutButtons.style.display = "none";

    } else {

        profileArea.style.display = "none";
        loggedOutButtons.style.display = "flex";
    }
});