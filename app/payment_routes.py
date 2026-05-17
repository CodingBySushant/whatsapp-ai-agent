# Add this to app/main.py after the existing routes

from fastapi import Query

@app.get("/payment/callback")
async def payment_callback(
    razorpay_payment_id: str = Query(...),
    razorpay_payment_link_id: str = Query(...),
    razorpay_payment_link_reference_id: str = Query(...),
    razorpay_payment_link_status: str = Query(...),
    razorpay_signature: str = Query(...)
):
    from app.payments import verify_payment
    from app.database import Database

    db = Database()

    # Extract booking_id from reference_id
    booking_id = int(razorpay_payment_link_reference_id.split("-")[-1]) if "-" in razorpay_payment_link_reference_id else None

    if razorpay_payment_link_status == "paid":
        is_valid = await verify_payment(razorpay_payment_id, razorpay_payment_link_id, razorpay_signature)
        if is_valid and booking_id:
            db.update_booking_status(booking_id, "confirmed", razorpay_payment_id)
            booking = db.get_booking(booking_id)

            # Send confirmation to customer
            receipt_msg = (
                f"✅ *Booking Confirmed!*\n\n"
                f"🎉 Nirvanta Travels mein aapka swagat hai!\n\n"
                f"📋 *Booking Details:*\n"
                f"Booking ID: #{booking_id}\n"
                f"Trip: {booking['trips']['name']}\n"
                f"Travel Date: {booking['travel_date']}\n"
                f"Adults: {booking['adults']} | Kids: {booking.get('kids', 0)}\n"
                f"Amount Paid: ₹{booking['total_amount']:,}\n"
                f"Payment ID: {razorpay_payment_id}\n\n"
                f"📞 Kisi bhi sawal ke liye hume call karein.\n"
                f"Safe travels! 🏔️✨"
            )
            await send_whatsapp_message(booking["customer_phone"], {
                "type": "text",
                "text": {"body": receipt_msg}
            })

            # Notify owner
            await notify_owner(
                f"✅ Payment Received!\nBooking #{booking_id}\n"
                f"Customer: {booking['customer_name']}\n"
                f"Amount: ₹{booking['total_amount']:,}\n"
                f"Payment ID: {razorpay_payment_id}"
            )

    return PlainTextResponse("Payment processed. Aap WhatsApp check karein!")
