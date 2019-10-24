package com.example.buzzbraceletvendor;

import com.google.gson.Gson;

public class HashableObject{
    public String getHash(){
        return Helper.getSHA256Hash(this.toJson());
    }
    public String toJson(){
        return new Gson().toJson(this);
    }
}