package com.example.buzzbraceletadmin;

import com.google.gson.*;

import java.util.Date;
import java.text.SimpleDateFormat;

public class Transaction extends HashableObject{
    int transaction;
    public String sender;
    public String address;
    public double amount;
    public String timestamp;
    public String signature;

    public Transaction(int t, String s, String r, double a){
        transaction = t;
        sender = s;
        address = r;
        amount = a;
        timestamp = new SimpleDateFormat("yyy-MM-dd'T'HH:mm:ss").format(new Date());
        signature = null;
    }

    public String getHash(){
        Transaction tmp = new Transaction(this.transaction, this.sender, this.address, this.amount);
        tmp.timestamp = this.timestamp;
        return Helper.getSHA256Hash(tmp.toJson());
    }

    public static Transaction fromJson(String j){
        return new Gson().fromJson(j, Transaction.class);
    }
}