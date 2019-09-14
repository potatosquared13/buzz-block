package testapp;

import com.google.gson.*;

public class HashableObject{
    public String getHash(){
        return Helper.getSHA256Hash(this.toJson());
    }
    public String toJson(){
        return new Gson().toJson(this);
    }
}