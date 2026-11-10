
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime
from pathlib import Path

# =====================================
# 1. KONFIGURASI
# =====================================

st.set_page_config(
    page_title="AKAK Finance",
    page_icon="💰",
    layout="wide"
)

DB_NAME = "finance.db"

CATEGORIES = [
    "Kos", "Makan", "Transportasi",
    "Pendidikan", "Internet", "Hiburan",
    "Kesehatan", "Belanja", "Lainnya"
]


# =====================================
# 2. DATABASE
# =====================================

def get_db():
    return sqlite3.connect(DB_NAME)


def initialize_database():

    with get_db() as db:

        db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            UNIQUE(month, category)
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            current REAL DEFAULT 0,
            deadline TEXT
        )
        """)


def load_data(query, params=()):

    with get_db() as db:
        return pd.read_sql_query(
            query, db, params=params
        )


initialize_database()


# =====================================
# 3. FUNGSI PENDUKUNG
# =====================================

def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


today = date.today()
current_month = today.strftime("%Y-%m")

transactions = load_data(
    "SELECT * FROM transactions"
)

month_data = transactions[
    transactions["date"].str.startswith(
        current_month
    )
] if not transactions.empty else transactions


income = month_data.loc[
    month_data["type"] == "income", "amount"
].sum()

expense = month_data.loc[
    month_data["type"] == "expense", "amount"
].sum()

balance = income - expense


# =====================================
# 4. SIDEBAR
# =====================================

st.sidebar.title("💰 AKAK Finance")
st.sidebar.caption("Asisten Keuangan Anak Kos")

page = st.sidebar.radio(
    "Navigasi",
    [
        "Dashboard",
        "Transaksi",
        "Anggaran",
        "Tabungan",
        "Analisis"
    ]
)

st.sidebar.divider()

st.sidebar.write("📅", today.strftime("%d-%m-%Y"))

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()


# =====================================
# 5. HALAMAN DASHBOARD
# =====================================

if page == "Dashboard":

    st.title("Dashboard Keuangan")
    st.caption("Ringkasan keuangan bulan ini")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Pemasukan",
        rupiah(income)
    )

    col2.metric(
        "Total Pengeluaran",
        rupiah(expense)
    )

    col3.metric(
        "Saldo Bersih Bulan Ini",
        rupiah(balance),
        delta=rupiah(balance)
    )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader("Pengeluaran per Kategori")

        expense_data = month_data[
            month_data["type"] == "expense"
        ]

        if not expense_data.empty:

            category_data = expense_data.groupby(
                "category"
            )["amount"].sum()

            fig, ax = plt.subplots()

            category_data.plot(
                kind="pie",
                autopct="%1.1f%%",
                ax=ax
            )

            ax.set_ylabel("")
            st.pyplot(fig)
            plt.close(fig)

        else:
            st.info("Belum ada pengeluaran.")

    with right:

        st.subheader("Transaksi Terbaru")

        if not month_data.empty:

            recent = month_data.sort_values(
                "date", ascending=False
            ).head(5)

            st.dataframe(
                recent[
                    ["date", "type", "category", "amount"]
                ],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("Belum ada transaksi.")

    st.divider()

    st.subheader("🤖 Rekomendasi Keuangan")

    if income > 0:

        ratio = expense / income * 100

        if ratio >= 100:
            st.error(
                "Pengeluaran sudah mencapai atau "
                "melebihi pemasukan. Evaluasi kebutuhan."
            )

        elif ratio >= 80:
            st.warning(
                "Pengeluaran sudah mencapai "
                f"{ratio:.1f}% dari pemasukan. "
                "Kurangi pengeluaran non-esensial."
            )

        else:
            st.success(
                f"Pengeluaran mencapai {ratio:.1f}% "
                "dari pemasukan. Tetap pantau anggaran!"
            )

    else:
        st.info("Masukkan pemasukan untuk memperoleh analisis.")


# =====================================
# 6. HALAMAN TRANSAKSI
# =====================================

elif page == "Transaksi":

    st.title("📝 Manajemen Transaksi")

    with st.form("transaction_form"):

        transaction_type = st.selectbox(
            "Jenis transaksi",
            ["income", "expense"],
            format_func=lambda x:
                "Pemasukan" if x == "income"
                else "Pengeluaran"
        )

        category = st.selectbox(
            "Kategori", CATEGORIES
        )

        amount = st.number_input(
            "Nominal (Rp)",
            min_value=0,
            step=1000
        )

        transaction_date = st.date_input(
            "Tanggal",
            value=today
        )

        description = st.text_input(
            "Keterangan"
        )

        submitted = st.form_submit_button(
            "Simpan Transaksi",
            use_container_width=True
        )

        if submitted:

            if amount <= 0:
                st.error("Nominal harus lebih dari nol.")

            else:

                with get_db() as db:

                    db.execute("""
                    INSERT INTO transactions
                    (date, type, category, amount, description)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        transaction_date.isoformat(),
                        transaction_type,
                        category,
                        amount,
                        description
                    ))

                st.success("Transaksi berhasil disimpan!")
                st.rerun()

    st.divider()

    st.subheader("Riwayat Transaksi")

    if not transactions.empty:

        st.dataframe(
            transactions.sort_values(
                "date", ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Belum ada transaksi.")


# =====================================
# 7. HALAMAN ANGGARAN
# =====================================

elif page == "Anggaran":

    st.title("📊 Manajemen Anggaran")

    month = st.text_input(
        "Periode anggaran (YYYY-MM)",
        value=current_month
    )

    try:
        datetime.strptime(month, "%Y-%m")
        valid_month = True
    except ValueError:
        valid_month = False
        st.error("Format bulan harus YYYY-MM.")

    if valid_month:

        with st.form("budget_form"):

            category = st.selectbox(
                "Kategori anggaran",
                CATEGORIES
            )

            amount = st.number_input(
                "Batas anggaran (Rp)",
                min_value=1000,
                step=10000
            )

            submitted = st.form_submit_button(
                "Simpan Anggaran"
            )

            if submitted:

                with get_db() as db:

                    db.execute("""
                    INSERT INTO budgets
                    (month, category, amount)
                    VALUES (?, ?, ?)
                    ON CONFLICT(month, category)
                    DO UPDATE SET amount = excluded.amount
                    """, (month, category, amount))

                st.success("Anggaran berhasil diperbarui!")
                st.rerun()

        budgets = load_data(
            "SELECT * FROM budgets WHERE month = ?",
            (month,)
        )

        st.subheader("Status Anggaran")

        if not budgets.empty:

            month_expenses = load_data("""
                SELECT category, SUM(amount) AS spent
                FROM transactions
                WHERE type = 'expense'
                AND date LIKE ?
                GROUP BY category
            """, (month + "%",))

            for _, budget in budgets.iterrows():

                category = budget["category"]
                limit = budget["amount"]

                matching = month_expenses[
                    month_expenses["category"] == category
                ]

                spent = (
                    matching["spent"].sum()
                    if not matching.empty else 0
                )

                progress = min(spent / limit, 1.0)

                st.write(f"**{category}**")
                st.progress(progress)

                st.caption(
                    f"Terpakai: {rupiah(spent)} / "
                    f"{rupiah(limit)}"
                )

                if spent > limit:
                    st.error("Anggaran terlampaui!")
                elif progress >= 0.8:
                    st.warning("Anggaran hampir habis.")
                else:
                    st.success("Anggaran masih aman.")

        else:
            st.info("Belum ada anggaran pada periode ini.")


# =====================================
# 8. HALAMAN TABUNGAN
# =====================================

elif page == "Tabungan":

    st.title("🐷 Target Tabungan")

    with st.form("saving_form"):

        name = st.text_input("Nama target")

        target = st.number_input(
            "Target tabungan (Rp)",
            min_value=1000,
            step=10000
        )

        deadline = st.date_input(
            "Tanggal target",
            value=today
        )

        submitted = st.form_submit_button(
            "Buat Target"
        )

        if submitted:

            if not name.strip() or target <= 0:
                st.error("Isi nama dan nominal target dengan benar.")

            else:

                with get_db() as db:

                    db.execute("""
                    INSERT INTO savings
                    (name, target, current, deadline)
                    VALUES (?, ?, 0, ?)
                    """, (
                        name.strip(),
                        target,
                        deadline.isoformat()
                    ))

                st.success("Target berhasil dibuat!")
                st.rerun()

    goals = load_data(
        "SELECT * FROM savings"
    )

    st.divider()

    if not goals.empty:

        for _, goal in goals.iterrows():

            st.subheader(goal["name"])

            progress = min(
                goal["current"] / goal["target"],
                1.0
            )

            st.progress(progress)

            st.write(
                f"{rupiah(goal['current'])} / "
                f"{rupiah(goal['target'])}"
            )

            st.caption(
                f"Deadline: {goal['deadline']}"
            )

            with st.form(f"deposit_{goal['id']}"):

                deposit = st.number_input(
                    "Tambah tabungan (Rp)",
                    min_value=0,
                    step=10000,
                    key=f"amount_{goal['id']}"
                )

                submit = st.form_submit_button(
                    "Tambah Tabungan"
                )

                if submit:

                    if deposit <= 0:
                        st.error("Nominal harus lebih dari nol.")

                    else:

                        with get_db() as db:

                            db.execute("""
                            UPDATE savings
                            SET current = current + ?
                            WHERE id = ?
                            """, (deposit, int(goal["id"])))

                        st.success("Tabungan diperbarui!")
                        st.rerun()

    else:
        st.info("Belum ada target tabungan.")


# =====================================
# 9. HALAMAN ANALISIS
# =====================================

elif page == "Analisis":

    st.title("📈 Analisis Keuangan")

    if not month_data.empty:

        expense_data = month_data[
            month_data["type"] == "expense"
        ]

        if not expense_data.empty:

            category_data = expense_data.groupby(
                "category"
            )["amount"].sum().sort_values(
                ascending=False
            )

            st.subheader("Pengeluaran Terbesar")

            st.bar_chart(category_data)

            st.subheader("Statistik Pengeluaran")

            col1, col2 = st.columns(2)

            col1.metric(
                "Rata-rata transaksi",
                rupiah(expense_data["amount"].mean())
            )

            col2.metric(
                "Jumlah transaksi",
                len(expense_data)
            )

            st.subheader("Prediksi Akhir Bulan")

            days_passed = today.day

            next_month = (
                date(today.year + (today.month == 12),
                     today.month % 12 + 1, 1)
            )

            days_in_month = (
                next_month - date(
                    today.year, today.month, 1
                )
            ).days

            prediction = (
                expense / days_passed
            ) * days_in_month

            st.metric(
                "Estimasi pengeluaran akhir bulan",
                rupiah(prediction)
            )

            st.caption(
                "Estimasi sederhana berdasarkan rata-rata "
                "pengeluaran per hari yang sudah berjalan."
            )

        else:
            st.info("Belum ada pengeluaran.")

    else:
        st.info("Belum ada data bulan ini.")

    st.divider()

    st.subheader("Unduh Laporan")

    if not month_data.empty:

        csv_data = month_data.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 Download laporan CSV",
            data=csv_data,
            file_name=f"laporan_{current_month}.csv",
            mime="text/csv"
        )

    else:
        st.info("Belum ada laporan untuk diunduh.")


# =====================================
# 10. FOOTER
# =====================================

st.sidebar.divider()
st.sidebar.caption("AKAK Finance v1.0")
st.sidebar.caption("Smart Financial Assistant")
