
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.3.0/firebase-app.js";

import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/12.3.0/firebase-auth.js";


// ================= FIREBASE CONFIG =================

const firebaseConfig = {
    apiKey: "YOUR_EXISTING_FIREBASE_API_KEY",
    authDomain: "wanderai-f84d2.firebaseapp.com",
    projectId: "wanderai-f84d2",
    storageBucket: "wanderai-f84d2.firebasestorage.app",
    messagingSenderId: "455628284395",
    appId: "1:455628284395:web:b857b488ea3b3fde2479ae",
    measurementId: "G-NXM612J1JY"
};


// ================= INITIALIZE FIREBASE =================

const app = initializeApp(firebaseConfig);

const auth = getAuth(app);

const googleProvider = new GoogleAuthProvider();


// ================= MESSAGE HELPER =================

function showMessage(message, type = "error") {

    const messageBox =
        document.getElementById("authMessage");

    if (!messageBox) {
        return;
    }

    messageBox.textContent = message;

    messageBox.style.color =
        type === "success" ? "green" : "red";

}


// ================= SIGN UP =================

window.signupUser = async function () {

    const email =
        document.getElementById("signupEmail")?.value.trim();

    const password =
        document.getElementById("signupPassword")?.value;


    if (!email || !password) {

        showMessage(
            "Please enter your email and password."
        );

        return;
    }


    if (password.length < 6) {

        showMessage(
            "Password must contain at least 6 characters."
        );

        return;
    }


    try {

        await createUserWithEmailAndPassword(
            auth,
            email,
            password
        );


        showMessage(
            "Account created successfully!",
            "success"
        );


        setTimeout(() => {

            window.location.href = "/";

        }, 800);


    } catch (error) {

        console.error("Signup error:", error);

        showMessage(
            getFirebaseErrorMessage(error)
        );

    }

};


// ================= LOGIN =================

window.loginUser = async function () {

    const email =
        document.getElementById("loginEmail")?.value.trim();

    const password =
        document.getElementById("loginPassword")?.value;


    if (!email || !password) {

        showMessage(
            "Please enter your email and password."
        );

        return;
    }


    try {

        await signInWithEmailAndPassword(
            auth,
            email,
            password
        );


        showMessage(
            "Login successful!",
            "success"
        );


        setTimeout(() => {

            window.location.href = "/";

        }, 500);


    } catch (error) {

        console.error("Login error:", error);

        showMessage(
            getFirebaseErrorMessage(error)
        );

    }

};


// ================= GOOGLE LOGIN =================

window.googleLogin = async function () {

    try {

        await signInWithPopup(
            auth,
            googleProvider
        );


        window.location.href = "/";


    } catch (error) {

        console.error(
            "Google login error:",
            error
        );


        showMessage(
            getFirebaseErrorMessage(error)
        );

    }

};


// ================= PROFILE MENU =================

window.toggleProfileMenu = function () {

    console.log("PROFILE CLICKED");

    const menu =
        document.getElementById("profileMenu");

    if (!menu) {

        console.log(
            "Profile menu element not found"
        );

        return;
    }


    menu.classList.toggle("active");

    console.log(
        "Profile menu:",
        menu.classList.contains("active")
    );

};


// ================= LOGOUT =================

window.logoutUser = async function () {

    try {

        await signOut(auth);

        window.location.href = "/";

    } catch (error) {

        console.error(
            "Logout error:",
            error
        );

    }

};


// ================= LOGIN WITH ANOTHER ACCOUNT =================

window.loginAnotherAccount = async function () {

    try {

        await signOut(auth);

        window.location.href = "/login";

    } catch (error) {

        console.error(
            "Account switch error:",
            error
        );

    }

};


// ================= AUTH STATE =================

onAuthStateChanged(
    auth,
    (user) => {

        const loggedOutButtons =
            document.getElementById(
                "loggedOutButtons"
            );

        const profileArea =
            document.getElementById(
                "profileArea"
            );

        const profileImage =
            document.getElementById(
                "profileImage"
            );

        const menuProfileImage =
            document.getElementById(
                "menuProfileImage"
            );

        const profileName =
            document.getElementById(
                "profileName"
            );

        const profileEmail =
            document.getElementById(
                "profileEmail"
            );


        // ================= LOGGED IN =================

        if (user) {

            console.log(
                "Logged in user:",
                user.email
            );


            // Hide Login / Sign Up

            if (loggedOutButtons) {

                loggedOutButtons.style.display =
                    "none";

            }


            // Show profile photo

            if (profileArea) {

                profileArea.style.display =
                    "flex";

            }


            // Get Google profile photo

            const photoURL =
                user.photoURL;


            if (photoURL) {

                if (profileImage) {

                    profileImage.src =
                        photoURL;

                }


                if (menuProfileImage) {

                    menuProfileImage.src =
                        photoURL;

                }

            } else {

                // Default profile image

                const defaultImage =
                    "https://ui-avatars.com/api/?name="
                    + encodeURIComponent(
                        user.email || "User"
                    )
                    + "&background=111827&color=ffffff";


                if (profileImage) {

                    profileImage.src =
                        defaultImage;

                }


                if (menuProfileImage) {

                    menuProfileImage.src =
                        defaultImage;

                }

            }


            // User name

            if (profileName) {

                profileName.textContent =
                    user.displayName ||
                    "WanderAI User";

            }


            // User email

            if (profileEmail) {

                profileEmail.textContent =
                    user.email || "";

            }

        }


        // ================= LOGGED OUT =================

        else {

            console.log(
                "No user logged in"
            );


            if (loggedOutButtons) {

                loggedOutButtons.style.display =
                    "flex";

            }


            if (profileArea) {

                profileArea.style.display =
                    "none";

            }

        }

    }
);


// ================= FIREBASE ERROR MESSAGES =================

function getFirebaseErrorMessage(error) {

    switch (error.code) {

        case "auth/email-already-in-use":

            return "This email is already registered.";

        case "auth/invalid-email":

            return "Please enter a valid email address.";

        case "auth/weak-password":

            return "Password is too weak.";

        case "auth/user-not-found":

            return "No account found with this email.";

        case "auth/wrong-password":

            return "Incorrect password.";

        case "auth/invalid-credential":

            return "Invalid email or password.";

        case "auth/popup-closed-by-user":

            return "Google login was cancelled.";

        case "auth/popup-blocked":

            return "Your browser blocked the Google login popup.";

        case "auth/unauthorized-domain":

            return "This website domain is not authorized in Firebase.";

        default:

            return error.message ||
                   "Something went wrong. Please try again.";

    }

}


// ================= CLOSE PROFILE MENU =================

document.addEventListener(
    "click",
    function (event) {

        const profileArea =
            document.getElementById(
                "profileArea"
            );

        const profileMenu =
            document.getElementById(
                "profileMenu"
            );


        if (!profileArea ||
            !profileMenu) {

            return;
        }


        if (!profileArea.contains(
            event.target
        )) {

            profileMenu.classList.remove(
                "active"
            );

        }

    }
);
